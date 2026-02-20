import json
import os
import signal
import uvicorn
import asyncio
from datetime import datetime
from typing import Dict
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles


class StaticFilesNo304(StaticFiles):
    """禁用 304 Not Modified，避免浏览器强缓存导致替换图片后仍显示旧图。"""
    def is_not_modified(self, *args, **kwargs) -> bool:
        return False
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, JSONResponse, Response
from starlette.background import BackgroundTask
from .shared import clients, set_current_character, conversation_history, add_client, remove_client, get_memory_system, set_current_account, get_current_account, get_last_memory_init_error
from .app_logic import start_conversation, stop_conversation, set_env_variable, characters_folder, set_transcription_model, fetch_ollama_models, load_character_prompt, load_character_specific_history
from .enhanced_logic import start_enhanced_conversation, stop_enhanced_conversation
from .app import send_message_to_clients
import logging
import subprocess
import sys
from pathlib import Path
from threading import Thread
import uuid
import aiohttp
import re
import shutil


def center_banner(banner_text: str) -> str:
    terminal_width = shutil.get_terminal_size((80, 20)).columns  # fallback = 80
    centered_lines = []
    for line in banner_text.splitlines():
        centered_line = line.center(terminal_width)
        centered_lines.append(centered_line)
    return "\n".join(centered_lines)

def display_banner():
    raw_banner = f"""

 ▌ ▐·      ▪   ▄▄· ▄▄▄ .     ▄▄·  ▄ .▄ ▄▄▄· ▄▄▄▄▄     ▄▄▄· ▪  
▪█·█▌▪     ██ ▐█ ▌▪▀▄.▀·    ▐█ ▌▪██▪▐█▐█ ▀█ •██      ▐█ ▀█ ██ 
▐█▐█• ▄█▀▄ ▐█·██ ▄▄▐▀▀▪▄    ██ ▄▄██▀▐█▄█▀▀█  ▐█.▪    ▄█▀▀█ ▐█·
 ███ ▐█▌.▐▌▐█▌▐███▌▐█▄▄▌    ▐███▌██▌▐▀▐█ ▪▐▌ ▐█▌·    ▐█ ▪▐▌▐█▌
. ▀   ▀█▄▀▪▀▀▀·▀▀▀  ▀▀▀     ·▀▀▀ ▀▀▀ · ▀  ▀  ▀▀▀      ▀  ▀ ▀▀▀

"""
    print(center_banner(raw_banner))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Display banner
display_banner()

app = FastAPI()


@app.on_event("startup")
async def startup_validate_dialogues():
    """启动时预加载 dialogues.json，并自动刷新场景索引与本地占位图"""
    try:
        from .scene_npc_db import get_dialogues, _dialogues_path, reload_dialogues
        path = _dialogues_path()
        data = get_dialogues()
        if data:
            logger.info("启动: dialogues.json 已加载，路径=%s，条数=%d", path, len(data))
        else:
            logger.warning("启动: dialogues.json 为空或未找到，路径=%s。可设置环境变量 VOICE_CHAT_PROJECT_ROOT 指定项目根目录", path)
    except Exception as e:
        logger.warning("启动: 预加载 dialogues 失败: %s", e)

    # 每次启动自动刷新场景索引与缺失场景的占位图（从 dialogues 生成索引并同步 app/static/images/scenes/）
    try:
        root = Path(__file__).resolve().parent.parent
        script = root / "scripts" / "build_scene_npc_index.py"
        if script.is_file():
            r = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if r.returncode == 0:
                logger.info("启动: 场景索引与本地图已刷新")
                reload_dialogues()
                from .scene_npc_db import _load_scene_index, clear_scene_image_url_cache
                _load_scene_index()
                clear_scene_image_url_cache()
            else:
                logger.warning("启动: 场景索引脚本执行异常 returncode=%s stderr=%s", r.returncode, (r.stderr or "").strip()[:200])
        else:
            logger.debug("启动: 未找到场景索引脚本 %s", script)
    except subprocess.TimeoutExpired:
        logger.warning("启动: 场景索引脚本超时")
    except Exception as e:
        logger.warning("启动: 执行场景索引脚本失败: %s", e)

    # 预加载场景索引（若存在），首请求即可用内存数据；并清空场景图 URL 缓存、打日志
    try:
        from .scene_npc_db import _load_scene_index, clear_scene_image_url_cache, _scenes_images_dir
        clear_scene_image_url_cache()
        scenes_dir = _scenes_images_dir()
        logger.info("启动: 场景图目录=%s, home.png存在=%s", scenes_dir, (scenes_dir / "home.png").is_file())
        if _load_scene_index():
            logger.info("启动: 场景索引已预加载")
    except Exception as e:
        logger.debug("启动: 预加载场景索引跳过: %s", e)


# Mount static files and templates（用项目根绝对路径；禁用 304 便于更新场景图后立即生效）
_project_root = Path(__file__).resolve().parent.parent
app.mount("/app/static", StaticFilesNo304(directory=str(_project_root / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(_project_root / "app" / "templates"))

# 添加音频文件服务
@app.get("/audio/{file_path:path}")
async def serve_audio(file_path: str):
    """提供音频文件服务"""
    import os
    from pathlib import Path
    
    # 构建音频文件路径
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_file_dir)
    audio_path = os.path.join(project_dir, "outputs", file_path)
    
    # 检查文件是否存在
    if os.path.exists(audio_path) and os.path.isfile(audio_path):
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            headers={"Content-Disposition": f"inline; filename={os.path.basename(audio_path)}"}
        )
    else:
        return JSONResponse(
            {"status": "error", "message": "Audio file not found"},
            status_code=404
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """默认显示英语学习页面"""
    character_name = os.getenv("CHARACTER_NAME", "english_tutor")
    return templates.TemplateResponse("voice_chat.html", {
        "request": request,
        "character_name": character_name,
    })

@app.get("/voice_chat", response_class=HTMLResponse)
async def get_voice_chat(request: Request):
    """Instagram风格的语音消息界面"""
    character_name = os.getenv("CHARACTER_NAME", "english_tutor")
    return templates.TemplateResponse("voice_chat.html", {
        "request": request,
        "character_name": character_name,
    })


# 真人 1v1 练习（同源 SPA）
_PRACTICE_LIVE_DIR = Path(__file__).resolve().parent / "static" / "practice-live"

# 画风与主站统一：注入的样式表与字体（theme 走专用路由，不缓存，改完即生效）
_PRACTICE_LIVE_THEME_CSS_URL = "/practice/live/theme.css"
_PRACTICE_LIVE_OVERRIDE_CSS_PATH = Path(__file__).resolve().parent / "static" / "css" / "practice-live-override.css"
_INTER_FONT_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
_503_HTML = (
    "<!DOCTYPE html><html><body style='font-family:sans-serif;padding:2rem;'>"
    "<h1>真人练习未就绪</h1>"
    "<p>请先在项目根目录执行 <code>npm run build:practice-live</code>，"
    "并将构建输出复制到 <code>app/static/practice-live/</code>。</p></body></html>"
)


def _practice_live_index_response() -> HTMLResponse:
    """返回注入统一画风后的 1v1 练习页 HTML；未构建则返回 503。"""
    index_path = _PRACTICE_LIVE_DIR / "index.html"
    if not index_path.is_file():
        return HTMLResponse(_503_HTML, status_code=503)
    html = index_path.read_text(encoding="utf-8")
    html = re.sub(
        r'<link[^>]+href="https://fonts\.googleapis\.com/css2\?[^"]*Cinzel[^"]*"[^>]*/?>\s*',
        "",
        html,
        flags=re.IGNORECASE,
    )
    # 覆盖样式走 theme.css 路由，服务端不缓存，修改 CSS 后刷新即可同步
    inject = (
        f'<link rel="stylesheet" href="{_INTER_FONT_URL}">'
        f'<link rel="stylesheet" href="{_PRACTICE_LIVE_THEME_CSS_URL}">'
    )
    if inject not in html:
        html = html.replace("</head>", inject + "\n</head>")
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/practice/live/theme.css", response_class=Response)
async def practice_live_theme_css():
    """1v1 练习页统一画风样式表，禁止缓存，修改后刷新即生效（含从 voice_chat 跳转进入）。"""
    if not _PRACTICE_LIVE_OVERRIDE_CSS_PATH.is_file():
        return Response(status_code=404)
    body = _PRACTICE_LIVE_OVERRIDE_CSS_PATH.read_bytes()
    return Response(
        content=body,
        media_type="text/css",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/practice/live", response_class=HTMLResponse)
async def practice_live_index():
    """真人 1v1 练习页入口；从 voice_chat 跳转至 /practice/live/chat 时也返回本注入页。"""
    return _practice_live_index_response()


@app.get("/practice/live/{full_path:path}", response_class=HTMLResponse)
async def practice_live_spa(full_path: str):
    """SPA：静态资源直接返回文件；其余路径（如 /chat）均返回注入统一画风后的 index.html。"""
    if not full_path or full_path == "index.html":
        return _practice_live_index_response()
    file_path = (_PRACTICE_LIVE_DIR / full_path).resolve()
    if not str(file_path).startswith(str(_PRACTICE_LIVE_DIR.resolve())):
        return HTMLResponse("<p>Invalid path</p>", status_code=400)
    if file_path.is_file():
        return FileResponse(file_path)
    return _practice_live_index_response()


@app.post("/api/account/login")
async def login_account(request: Request):
    """账号登录/创建"""
    try:
        data = await request.json()
        account_name = data.get("account_name", "").strip()
        
        if not account_name:
            return JSONResponse({
                "status": "error",
                "message": "账号名称不能为空"
            }, status_code=400)
        
        # 验证账号名称（只允许字母、数字、中文、下划线、连字符和空格）
        import re
        if not re.match(r'^[\w\s\u4e00-\u9fa5-]+$', account_name):
            return JSONResponse({
                "status": "error",
                "message": "账号名称只能包含字母、数字、中文、下划线和连字符"
            }, status_code=400)
        
        if len(account_name) > 20:
            return JSONResponse({
                "status": "error",
                "message": "账号名称不能超过20个字符"
            }, status_code=400)
        
        # 设置当前账号并初始化记忆系统
        set_current_account(account_name)
        memory_system = get_memory_system(account_name)
        
        if memory_system:
            return JSONResponse({
                "status": "success",
                "message": "登录成功",
                "account_name": account_name
            })
        else:
            detail = get_last_memory_init_error() or "未知原因"
            return JSONResponse({
                "status": "error",
                "message": f"初始化记忆系统失败：{detail}"
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"Error logging in account: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"登录失败: {str(e)}"
        }, status_code=500)

@app.get("/api/account/current")
async def get_current_account_info():
    """获取当前账号信息"""
    try:
        account_name = get_current_account()
        if account_name:
            return JSONResponse({
                "status": "success",
                "account_name": account_name
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": "未登录"
            }, status_code=401)
    except Exception as e:
        logger.error(f"Error getting current account: {e}")
        return JSONResponse({
            "status": "error",
            "message": f"获取账号信息失败: {str(e)}"
        }, status_code=500)

@app.post("/api/account/logout")
async def logout_account():
    """退出当前账号"""
    try:
        set_current_account(None)
        return JSONResponse({
            "status": "success",
            "message": "已退出账号"
        })
    except Exception as e:
        logger.error(f"Error logging out account: {e}")
        return JSONResponse({
            "status": "error",
            "message": f"退出失败: {str(e)}"
        }, status_code=500)

@app.get("/characters")
async def get_characters():
    if not os.path.exists(characters_folder):
        logger.warning(f"Characters folder not found: {characters_folder}")
        return {"characters": ["Assistant"]}  # fallback
    
    try:
        character_dirs = [d for d in os.listdir(characters_folder) 
                        if os.path.isdir(os.path.join(characters_folder, d))]
        if not character_dirs:
            logger.warning("No character folders found")
            return {"characters": ["Assistant"]}  # fallback
        return {"characters": character_dirs}
    except Exception as e:
        logger.error(f"Error listing characters: {e}")
        return {"characters": ["Assistant"]}  # fallback in case of error

@app.get("/elevenlabs_voices")
async def get_elevenlabs_voices():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    voices_file = os.path.join(project_dir, 'elevenlabs_voices.json')
    example_file = os.path.join(project_dir, 'elevenlabs_voices.json.example')
    
    # If the elevenlabs_voices.json file doesn't exist but the example does, create from example
    if not os.path.exists(voices_file) and os.path.exists(example_file):
        try:
            logger.info("elevenlabs_voices.json not found. Creating from example file.")
            with open(example_file, 'r', encoding='utf-8') as src:
                with open(voices_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            logger.info("Created elevenlabs_voices.json from example file.")
        except Exception as e:
            logger.error(f"Error creating elevenlabs_voices.json: {e}")
            
    # If file still doesn't exist, create a minimal version
    if not os.path.exists(voices_file):
        try:
            logger.info("Creating minimal elevenlabs_voices.json.")
            default_content = {
                "voices": {},
                "_comment": "This is a placeholder file. Replace with your own voice IDs from ElevenLabs."
            }
            with open(voices_file, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, indent=2)
            logger.info("Created minimal elevenlabs_voices.json file.")
        except Exception as e:
            logger.error(f"Error creating minimal elevenlabs_voices.json: {e}")
            return {"voices": []}
    
    try:
        with open(voices_file, 'r', encoding='utf-8') as f:
            voices = json.load(f)
        return voices
    except Exception as e:
        logger.error(f"Error reading elevenlabs_voices.json: {e}")
        return {"voices": []}

@app.get("/enhanced", response_class=HTMLResponse)
async def get_enhanced(request: Request):
    return templates.TemplateResponse("enhanced.html", {"request": request})

@app.get("/scenes", response_class=HTMLResponse)
async def list_scenes(request: Request):
    """展示可进入的沉浸式场景列表（简单实现）"""
    # 简单示例场景清单，后续可基于用户记忆/已掌握场景动态生成
    scenes = [
        {
            "id": "cafe",
            "title": "咖啡馆",
            "image": "https://placehold.co/1200x800?text=Coffee+Shop"
        }
    ]
    return templates.TemplateResponse("scene_list.html", {"request": request, "scenes": scenes})


@app.get("/scene/{scene_id}", response_class=HTMLResponse)
async def get_scene(request: Request, scene_id: str):
    """渲染单个场景页面（背景 + NPC 按钮 + 简单对话弹窗）"""
    # 简单配置：针对 scene_id 返回背景图与 NPC 列表
    scenes_config = {
        "cafe": {
            "title": "咖啡馆",
            # 使用外部占位图，用户可以替换为本地文件：/app/static/images/cafe.jpg
            "image": "https://placehold.co/1200x800?text=Coffee+Shop",
            "npcs": [
                {"id": "waiter", "label": "服务员", "hint": "点我用英语点单", "character": "cafe_waiter"},
                {"id": "customer_a", "label": "顾客 A", "hint": "点我和陌生人聊天", "character": "cafe_customer_a"},
                {"id": "customer_b", "label": "顾客 B", "hint": "点我和陌生人聊天", "character": "cafe_customer_b"}
            ]
        }
    }
    scene = scenes_config.get(scene_id, scenes_config["cafe"])
    return templates.TemplateResponse("scene.html", {"request": request, "scene": scene})


def _scene_account(request: Request, account_name: str = None) -> str:
    """解析场景相关 API 的当前账户：X-Account-Name 头 > account_name 查询 > get_current_account()。确保多进程/未建 WebSocket 时前端传参仍能命中 Supabase 进度。"""
    header_acc = (request.headers.get("X-Account-Name") or "").strip()
    query_acc = (account_name or "").strip()
    return header_acc or query_acc or get_current_account() or ""


@app.get("/api/scene-list")
async def api_list_scenes(request: Request, account_name: str = None):
    """Return immersive scenes (unlocked only) for modal. 支持 account_name 查询或 X-Account-Name 头。"""
    from .scene_npc_db import get_immersive_scene_list
    acc = _scene_account(request, account_name)
    scenes = get_immersive_scene_list(acc)
    return JSONResponse({"scenes": scenes})


@app.get("/api/scenes/{scene_id}")
async def api_get_scene(request: Request, scene_id: str, account_name: str = None):
    """Return immersive scene detail with NPCs. 支持 account_name 查询或 X-Account-Name 头。"""
    from .scene_npc_db import get_immersive_scene_detail
    acc = _scene_account(request, account_name)
    scene = get_immersive_scene_detail(scene_id, acc)
    if not scene:
        return JSONResponse({"error": "scene not found or not unlocked"}, status_code=404)
    return JSONResponse({"scene": scene})


# --- 真人 1v1 练习：解锁场景列表 + 按场景取一条对话（角色/任务/台词）---

@app.get("/api/practice-live/unlocked-scenes")
async def api_practice_live_unlocked_scenes(request: Request, account_name: str = None):
    """返回当前账号已解锁的 small_scene_id 列表，供匹配时取交集/并集选主题。"""
    acc = _scene_account(request, account_name)
    from .scene_npc_db import get_unlocked_scenes
    ids = get_unlocked_scenes(acc) if acc else []
    return JSONResponse({"small_scene_ids": ids})


@app.get("/api/practice-live/dialogue")
async def api_practice_live_dialogue(request: Request, small_scene_id: str):
    """返回该小场景下一条沉浸式对话，含角色名、任务、A/B 台词选项（用于 1v1 房间内展示）。"""
    from .scene_npc_db import get_one_immersive_dialogue_for_scene
    d = get_one_immersive_dialogue_for_scene(small_scene_id.strip())
    if not d:
        return JSONResponse({"error": "no dialogue for scene"}, status_code=404)
    content = d.get("content") or []
    npc_name = (d.get("npc_name") or "").strip() or "角色A"
    # 约定：A = NPC 方，B = 学习者方
    role_label_a = npc_name
    role_label_b = "学习者"
    lines_a = [x for x in content if x.get("role") == "A"]
    lines_b = [x for x in content if x.get("role") == "B"]
    return JSONResponse({
        "small_scene_id": d.get("small_scene"),
        "small_scene_name": d.get("small_scene_name"),
        "npc_name": npc_name,
        "role_label_a": role_label_a,
        "role_label_b": role_label_b,
        "task_a": d.get("user_goal_a") or d.get("core_sentences") or "",
        "task_b": d.get("user_goal") or d.get("core_sentences") or "",
        "core_sentences": d.get("core_sentences"),
        "lines_a": [{"content": x.get("content"), "hint": x.get("hint")} for x in lines_a],
        "lines_b": [{"content": x.get("content"), "hint": x.get("hint")} for x in lines_b],
    })


# --- 场景-NPC 学习 API ---

@app.get("/api/scene-npc/check")
async def api_scene_npc_check():
    """检查 dialogues.json 是否加载成功（用于排查「暂无可用场景」）"""
    from .scene_npc_db import get_dialogues, _dialogues_path
    path = _dialogues_path()
    dialogues = get_dialogues()
    return JSONResponse({
        "ok": len(dialogues) > 0,
        "count": len(dialogues),
        "path": str(path),
        "path_exists": path.exists(),
    })


@app.get("/api/scene-npc/debug-scene-images")
async def api_debug_scene_images():
    """排查场景图不更新：返回后端实际使用的图片目录及 home.png 等是否存在。"""
    from .scene_npc_db import _scenes_images_dir, _scene_image_url
    base = _scenes_images_dir()
    sample_ids = ["home", "bank", "cafe"]
    files = {sid: {ext: (base / f"{sid}{ext}").is_file() for ext in [".png", ".svg"]} for sid in sample_ids}
    urls = {sid: _scene_image_url(sid) for sid in sample_ids}
    return JSONResponse({
        "images_dir": str(base),
        "dir_exists": base.exists(),
        "sample_files": files,
        "sample_urls": urls,
    })


@app.get("/api/scene-npc/big-scenes")
async def api_big_scenes():
    from .scene_npc_db import get_big_scenes_with_immersive, get_dialogues, _dialogues_path
    # 仅返回其下至少有一个 immersive 小场景的大场景（严格贴合 dialogues.json）
    big_scenes = get_big_scenes_with_immersive()
    path = _dialogues_path()
    dialogues = get_dialogues()
    if not big_scenes:
        logger.warning("big-scenes 为空，path=%s exists=%s count=%d",
                       path, path.exists(), len(dialogues))
        return JSONResponse({
            "big_scenes": [],
            "_debug": {"path": str(path), "path_exists": path.exists(), "loaded_count": len(dialogues)}
        })
    return JSONResponse({"big_scenes": big_scenes})


@app.get("/api/scene-npc/small-scenes")
async def api_small_scenes(big_scene_id: str):
    from .scene_npc_db import get_small_scenes_by_big
    scenes = get_small_scenes_by_big(big_scene_id)
    return JSONResponse({"small_scenes": scenes})


@app.get("/api/scene-npc/immersive-small-scenes")
async def api_immersive_small_scenes(request: Request, big_scene_id: str, account_name: str = None):
    """返回某大场景下、有沉浸式内容的小场景列表。支持 account_name 查询或 X-Account-Name 头。"""
    from .scene_npc_db import get_immersive_small_scenes_by_big
    acc = _scene_account(request, account_name)
    scenes = get_immersive_small_scenes_by_big(big_scene_id, acc)
    return JSONResponse({"scenes": scenes})


@app.get("/api/scene-npc/npcs")
async def api_npcs(request: Request, small_scene_id: str, account_name: str = None):
    """返回小场景下的 NPC 列表，含 learned 状态。account 优先从 X-Account-Name 头或 account_name 查询参数获取。"""
    from .scene_npc_db import get_npcs_by_small_scene, get_npc_progress, get_learn_dialogue
    npcs = get_npcs_by_small_scene(small_scene_id)
    header_acc = (request.headers.get("X-Account-Name") or "").strip()
    query_acc = (account_name or "").strip()
    account = header_acc or query_acc or get_current_account() or ""
    progress_data = get_npc_progress(account)
    progress = set(progress_data.get(small_scene_id, []))
    result = []
    for n in npcs:
        has_learn = get_learn_dialogue(small_scene_id, n["id"]) is not None
        result.append({
            **n,
            "learned": n["id"] in progress,
            "has_content": has_learn
        })
    return JSONResponse({
        "npcs": result,
        "_debug": {"account": account or "(empty)", "small_scene_id": small_scene_id, "progress_list": list(progress)}
    })


@app.get("/api/scene-npc/dialogue/learn")
async def api_dialogue_learn(small_scene_id: str, npc_id: str):
    from .scene_npc_db import get_learn_dialogue
    d = get_learn_dialogue(small_scene_id, npc_id)
    if not d:
        return JSONResponse({"error": "dialogue not found"}, status_code=404)
    return JSONResponse({"dialogue": d})


@app.get("/api/scene-npc/dialogue/review")
async def api_dialogue_review(small_scene_id: str, npc_id: str):
    from .scene_npc_db import get_review_dialogue
    d = get_review_dialogue(small_scene_id, npc_id)
    if not d:
        return JSONResponse({"error": "dialogue not found"}, status_code=404)
    return JSONResponse({"dialogue": d})


@app.get("/api/scene-npc/dialogue/immersive")
async def api_dialogue_immersive(request: Request, small_scene_id: str, npc_id: str, account_name: str = None):
    from .scene_npc_db import get_immersive_dialogue, get_npc_progress, _safe_account
    acc = _scene_account(request, account_name)
    progress = get_npc_progress(_safe_account(acc))
    learned = set(progress.get(small_scene_id, []))
    if npc_id not in learned:
        return JSONResponse(
            {"error": "未解锁", "message": "请先在学习页完成该角色的对话学习后再体验沉浸对话"},
            status_code=403
        )
    d = get_immersive_dialogue(small_scene_id, npc_id)
    if not d:
        return JSONResponse({"error": "dialogue not found"}, status_code=404)
    # 确保前端一定能拿到 user_goal / user_goal_a（键名与类型一致）
    out = dict(d)
    out.setdefault("user_goal", "")
    out.setdefault("user_goal_a", "")
    return JSONResponse({"dialogue": out})


@app.post("/api/scene-npc/mark-learned")
async def api_mark_learned(request: Request):
    from .scene_npc_db import mark_npc_learned, check_and_unlock_scene
    data = await request.json()
    small_scene_id = (data.get("small_scene_id") or "").strip()
    npc_id = (data.get("npc_id") or "").strip()
    if not small_scene_id or not npc_id:
        return JSONResponse({"status": "error", "message": "missing small_scene_id or npc_id"}, status_code=400)
    account_name = get_current_account() or ""
    mark_npc_learned(account_name, small_scene_id, npc_id)
    newly_unlocked = check_and_unlock_scene(account_name, small_scene_id)
    return JSONResponse({"status": "success", "newly_unlocked": newly_unlocked})


# ---------- 沉浸式自由对话：与 AI 按剧本流程对话，可适当扩展，任务完成即结束，跑偏则纠正 ----------
@app.post("/api/scene-npc/immersive-chat")
async def api_immersive_chat(request: Request):
    """沉浸式自由对话：AI 按 immersive 剧本推进，可换表达，任务完成即结束，话题跑偏时纠正。"""
    try:
        from .scene_npc_db import get_immersive_dialogue, get_npc_progress, _safe_account
        from .app import chatgpt_streamed_async

        data = await request.json()
        small_scene_id = (data.get("small_scene_id") or "").strip()
        npc_id = (data.get("npc_id") or "").strip()
        user_message = (data.get("message") or "").strip()
        history = data.get("history") or []  # [{ "role": "user"|"assistant", "content": "..." }]
        role_swapped = data.get("role_swapped") is True  # True=用户演A(NPC)，AI演B

        if not small_scene_id or not npc_id:
            return JSONResponse({"status": "error", "message": "missing small_scene_id or npc_id"}, status_code=400)

        acc = _scene_account(request, data.get("account_name"))
        progress = get_npc_progress(_safe_account(acc))
        if npc_id not in (progress.get(small_scene_id) or []):
            return JSONResponse({"error": "未解锁", "message": "请先完成该角色学习"}, status_code=403)

        dialogue = get_immersive_dialogue(small_scene_id, npc_id)
        if not dialogue or not dialogue.get("content"):
            return JSONResponse({"status": "error", "message": "未找到该场景对话"}, status_code=404)

        npc_name = dialogue.get("npc_name") or npc_id
        small_scene_name = dialogue.get("small_scene_name") or small_scene_id
        content = dialogue["content"]
        script_lines = "\n".join([f"{item.get('role', 'A')}: {item.get('content', '')}" for item in content])
        core_sentences = dialogue.get("core_sentences") or ""
        core_chunks = dialogue.get("core_chunks") or ""

        if role_swapped:
            task_desc = f"用户扮演 NPC（{npc_name}），你扮演学习者（B）。请按剧本流程推进，直到学习者（你）完成剧本中 B 该做的所有事项，然后结束对话。"
        else:
            task_desc = f"你扮演 NPC（{npc_name}），用户扮演学习者（B）。请按剧本流程推进，直到用户完成剧本中 B 该做的所有事项，然后结束对话。"

        system = f"""You are in an English immersive scene: {small_scene_name}, NPC: {npc_name}.

【你的核心任务】
{task_desc}

【参考剧本（作为框架，可扩充）】
{script_lines}

【扩充轮数：自然、有逻辑地加内容，引导用户开口】
- 在剧本主线之外，自然增加几轮符合场景、符合角色的小对话，让用户多开口。例如：外卖员送餐可自然问一句天气或「今天忙吗」再回到确认房间、付款；家人吃饭可先问「今天过得怎么样」或「工作/学校有什么事」再接到要不要帮忙、洗菜、砧板在哪等。目的是引导用户多说，而不是把原本一轮要说的内容拆成多条短句发出去。
- 中途可以稍微偏离主线（加一点寒暄、关心），但背景和角色逻辑不变：外卖员最终仍完成送餐/签收/道别，家人场景最终仍落到帮忙洗菜、道谢等。整段对话的结果不脱离该场景、该角色。

【每轮不要太长，避免 AI 持续输出】
- 每一轮你的回复控制在 1～2 句以内，禁止写一大段。宁可一句短问或短接话，等用户说。否则会变成你在持续输出、用户没机会开口。
- 你的每一句必须与用户当前/之前说过的话衔接，不能跳过前提。用户明显跑题时礼貌拉回；剧本中 B 方该做的全部事项都完成后，再结束。

【规则】
1. 回复用英文。按剧本顺序与关键节点推进，用自然增加的小话题扩充轮数，让用户多说话；每轮回复严禁超过 2 句。
2. 当你判定用户已完成剧本中 B 方该做的全部事项且对话可收束时，在当条回复末尾单独一行输出 [IMMERSIVE_END]。
3. 除结束标记外不要输出 [IMMERSIVE_END] 或其它元指令。
"""
        if core_sentences or core_chunks:
            system += f"\n【本场景核心句/词块】\nSentences: {core_sentences}\nChunks: {core_chunks}\n"

        conv = []
        for h in history[-20:]:
            r = h.get("role")
            c = (h.get("content") or "").strip()
            if r and c and r in ("user", "assistant"):
                conv.append({"role": "user" if r == "user" else "assistant", "content": c})

        response = await chatgpt_streamed_async(user_message, system, "", conv)
        if not response:
            return JSONResponse({"status": "error", "message": "AI 未返回"}, status_code=500)

        task_completed = "[IMMERSIVE_END]" in response
        reply = response.replace("[IMMERSIVE_END]", "").strip()

        audio_url = None
        if reply:
            try:
                import uuid
                import os
                current_file_dir = os.path.dirname(os.path.abspath(__file__))
                project_dir = os.path.dirname(current_file_dir)
                immersive_dir = os.path.join(project_dir, "outputs", "immersive")
                os.makedirs(immersive_dir, exist_ok=True)
                filename = f"reply_{uuid.uuid4().hex[:12]}.wav"
                path = os.path.join(immersive_dir, filename)
                text_for_tts = (reply or "")[:500]
                if text_for_tts:
                    from .app import generate_speech
                    ok = await generate_speech(text_for_tts, path)
                    if ok and os.path.exists(path):
                        audio_url = f"/audio/immersive/{filename}"
            except Exception as tts_err:
                logger.warning(f"Immersive TTS failed: {tts_err}")

        return JSONResponse({
            "status": "success",
            "reply": reply,
            "task_completed": task_completed,
            "audio_url": audio_url,
        })
    except Exception as e:
        logger.error(f"Immersive chat error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/api/scene-npc/immersive-chat/report")
async def api_immersive_chat_report(request: Request):
    """沉浸式对话结束后：根据用户 transcript 生成纠错报告 + 剧本 + 核心句/词块，纯文本无语音。"""
    try:
        from .scene_npc_db import get_immersive_dialogue
        from .app import chatgpt_streamed_async

        data = await request.json()
        small_scene_id = (data.get("small_scene_id") or "").strip()
        npc_id = (data.get("npc_id") or "").strip()
        transcript = data.get("transcript") or []  # [{ "role": "user"|"assistant", "content": "..." }]

        if not small_scene_id or not npc_id:
            return JSONResponse({"status": "error", "message": "missing small_scene_id or npc_id"}, status_code=400)

        dialogue = get_immersive_dialogue(small_scene_id, npc_id)
        if not dialogue:
            return JSONResponse({"status": "error", "message": "未找到该场景对话"}, status_code=404)

        script_lines = []
        for item in dialogue.get("content") or []:
            script_lines.append(f"{item.get('role', 'A')}: {item.get('content', '')}")
        script_text = "\n".join(script_lines)
        core_sentences = dialogue.get("core_sentences") or ""
        core_chunks = dialogue.get("core_chunks") or ""

        user_lines = [t.get("content", "").strip() for t in transcript if (t.get("role") == "user" and t.get("content", "").strip())]
        user_text = "\n".join(user_lines) if user_lines else "(无用户发言)"

        scene_ctx = f"{dialogue.get('small_scene_name') or small_scene_id}，用户扮演学习者（B），NPC 为{dialogue.get('npc_name') or npc_id}。剧本大意：B 需按顺序完成打招呼、进入场景关键步骤（如送餐确认房间、报价收款）、道别等。"

        prompt = f"""场景说明：{scene_ctx}

用户在本场景中的整段发言：
{user_text}

请输出一份「复习纠错资料」报告，要求：

一、纠错与改进（报告主体，对口语提升有帮助的内容）
- 对用户发言做口语层面的纠错与改进建议：语法、用词、逻辑、表达自然度。忽略大小写和标点。
- 每条简短一行，格式：「原句 → 建议说法」或「某句可改为：…」，并可选一句简要说明（如语法点、更自然的说法）。
- 不要以「是否按场景/角色完成步骤」作为主要纠错内容。即使有句子与场景关系不大，也请从语法、用词、逻辑上给出改进建议；若确需提醒场景，可在一句内简短带过即可，不要整段只写「未按场景推进」之类、而不给语言层面的建议。
- 若用户发言很少或难以逐句纠错，可给 1～2 条通用表达建议或本场景常用说法。

二、本场景参考
- 仅列出本场景常用句型和词块，便于复习。
- 核心句：{core_sentences}
- 核心词块：{core_chunks}

格式要求：用「纠错与改进」和「本场景参考」两个小标题，下面用简短分条，排版清晰，不要长段落。不要 JSON 或代码块。
"""

        report = await chatgpt_streamed_async(
            prompt,
            "你是英语口语复习资料助手。报告主体应为语法、用词、逻辑、表达自然度等对口语提升有帮助的纠错与改进建议；不要以「是否按场景/角色完成步骤」为主要内容。分两段、分条简洁、排版清晰。",
            "",
            [],
        )
        if not report or not report.strip():
            report = "纠错与改进\n暂无。\n\n本场景参考\n核心句：" + core_sentences + "\n核心词块：" + core_chunks

        return JSONResponse({
            "status": "success",
            "report_markdown": report.strip(),
            "reference_script": script_text,
            "core_sentences": core_sentences,
            "core_chunks": core_chunks,
        })
    except Exception as e:
        logger.error(f"Immersive report error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/enhanced_defaults")
async def get_enhanced_defaults():
    from .enhanced_logic import enhanced_voice, enhanced_model, enhanced_tts_model, enhanced_transcription_model
    from .shared import get_current_character
    
    return {
        "character": get_current_character(),
        "voice": enhanced_voice,
        "model": enhanced_model,
        "tts_model": enhanced_tts_model,
        "transcription_model": enhanced_transcription_model
    }

@app.post("/set_character")
async def set_character(request: Request):
    try:
        data = await request.json()
        character = data.get("character")
        if not character:
            return {"status": "error", "message": "Character name is required"}
        
        # Import the set_character function from app_logic
        from .app_logic import set_api_character
        from pydantic import BaseModel
        
        # Create a model for the function
        class CharacterModel(BaseModel):
            character: str
        
        # Call the function with the character model
        result = await set_api_character(CharacterModel(character=character))
        return result
    except Exception as e:
        print(f"Error setting character: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/start_conversation")
async def start_conversation_route():
    Thread(target=lambda: asyncio.run(start_conversation())).start()
    return {"status": "started"}

@app.post("/stop_conversation")
async def stop_conversation_route():
    await stop_conversation()
    return {"status": "stopped"}

@app.post("/start_enhanced_conversation")
async def start_enhanced_conversation_route(request: Request):
    data = await request.json()
    character = data.get("character")
    speed = data.get("speed")
    model = data.get("model")
    voice = data.get("voice")
    tts_model = data.get("ttsModel")
    transcription_model = data.get("transcriptionModel")
    
    asyncio.create_task(start_enhanced_conversation(
        character=character,
        speed=speed,
        model=model,
        voice=voice,
        ttsModel=tts_model,
        transcriptionModel=transcription_model
    ))
    
    return {"status": "started"}

@app.post("/stop_enhanced_conversation")
async def stop_enhanced_conversation_route():
    await stop_enhanced_conversation()
    return {"status": "stopped"}

@app.post("/clear_history")
async def clear_history():
    """Clear the conversation history."""
    try:
        # Import with alias to avoid potential shadowing issues
        from .shared import conversation_history, get_current_character as get_character
        
        current_character = get_character()
        
        # Check if this is a story or game character
        is_story_character = current_character.startswith("story_") or current_character.startswith("game_")
        print(f"Clearing history for {current_character} ({is_story_character=})")
        
        # Clear the in-memory history
        conversation_history.clear()
        
        if is_story_character:
            # Clear character-specific history file
            character_dir = os.path.join(characters_folder, current_character)
            history_file = os.path.join(character_dir, "conversation_history.txt")
            
            if os.path.exists(history_file):
                os.remove(history_file)
                print(f"Deleted character-specific history file for {current_character}")
            
            # Write empty history to character-specific file
            from .app_logic import save_character_specific_history
            save_character_specific_history(conversation_history, current_character)
        # 不再处理全局历史文件（conversation_history.txt 已移除）
        
        return {"status": "cleared"}
    except Exception as e:
        print(f"Error clearing history: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/download_history")
async def download_history():
    # Create a temporary file with a unique name different from the main history file
    temp_file = f"temp_download_{uuid.uuid4().hex}.txt"
    
    # Format it the same way as the save_conversation_history function in app.py
    with open(temp_file, "w", encoding="utf-8") as file:
        for message in conversation_history:
            role = message["role"].capitalize()
            content = message["content"]
            file.write(f"{role}: {content}\n")
    
    # Return the file and ensure it will be cleaned up after sending
    return FileResponse(
        temp_file,
        media_type="text/plain",
        filename="conversation_history.txt",
        background=BackgroundTask(lambda: os.remove(temp_file) if os.path.exists(temp_file) else None)
    )

@app.get("/download_enhanced_history")
async def download_enhanced_history():
    """Download the conversation history."""
    try:
        # Import with alias to avoid potential shadowing issues
        from .shared import get_current_character as get_character
        
        current_character = get_character()
        
        # Check if this is a story or game character
        is_story_character = current_character.startswith("story_") or current_character.startswith("game_")
        print(f"Downloading history for {current_character} ({is_story_character=})")
        
        if is_story_character:
            # Get from character-specific history file
            character_dir = os.path.join(characters_folder, current_character)
            history_file = os.path.join(character_dir, "conversation_history.txt")
            
            if not os.path.exists(history_file) or os.path.getsize(history_file) == 0:
                # Create an empty history file if it doesn't exist
                with open(history_file, "w", encoding="utf-8") as f:
                    f.write(f"No conversation history found for {current_character}.\n")
                
            # Generate download filename based on character
            download_filename = f"{current_character}_history.txt"
            
            return FileResponse(
                history_file,
                media_type="text/plain",
                filename=download_filename
            )
        else:
            # 全局历史文件已移除，返回空文件
            temp_file = f"temp_download_{uuid.uuid4().hex}.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write("对话历史功能已移除，请使用记忆系统。\n")
            
            return FileResponse(
                temp_file,
                media_type="text/plain",
                filename="conversation_history.txt",
                background=BackgroundTask(lambda: os.remove(temp_file) if os.path.exists(temp_file) else None)
            )
    except Exception as e:
        print(f"Error downloading history: {e}")
        return PlainTextResponse(f"Error downloading history: {str(e)}", status_code=500)

@app.post("/set_transcription_model")
async def update_transcription_model(request: Request):
    data = await request.json()
    model_name = data.get("model")
    if not model_name:
        return {"status": "error", "message": "Model name is required"}
    
    return set_transcription_model(model_name)

@app.get("/ollama_models")
async def get_ollama_models():
    """
    Fetch available models from Ollama
    """
    return await fetch_ollama_models()

@app.get("/openai_ephemeral_key")
async def get_openai_ephemeral_key():
    """
    Generate an ephemeral key for OpenAI API access from the browser
    
    In a production environment, you would use a service like Supabase or a proper server-side
    authentication system. For simplicity in this demo, we're just returning the API key directly.
    """
    try:
        # Get the API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            logger.error("OPENAI_API_KEY not set in environment")
            return {"error": "API key not configured"}
        
        # In a real application, you might want to create a temporary token or session
        # For this demo, we'll just return the key directly
        # WARNING: This exposes your API key in production!
        
        # Add logging to help debug
        logger.info(f"Returning ephemeral key (first 5 chars): {api_key[:5]}...")
        
        # Return in the exact format expected by the WebRTC client
        return {
            "client_secret": {
                "value": api_key
            }
        }
    except Exception as e:
        logger.error(f"Error generating ephemeral key: {e}")
        return {"error": str(e)}

@app.post("/openai_realtime_proxy")
async def proxy_openai_realtime(request: Request):
    """
    Proxy endpoint to relay WebRTC connection to OpenAI API.
    This avoids CORS issues when connecting directly from the browser.
    """
    try:
        # Get the API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Get the SDP from the request body
        body = await request.body()
        sdp = body.decode('utf-8')
        
        # Get the model parameter from query params or default from environment
        default_model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview-2024-12-17")
        model = request.query_params.get('model', default_model)
        
        # Log the request (without the full SDP for privacy)
        logger.info(f"Proxying WebRTC connection to OpenAI Realtime API for model: {model}")
        
        # Forward to OpenAI
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.openai.com/v1/realtime?model={model}",
                content=sdp,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/sdp",
                    "OpenAI-Beta": "realtime=v1"
                }
            )
            
            # Return the same status code and content
            from fastapi.responses import Response
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type="application/sdp"
            )
    
    except Exception as e:
        logger.error(f"Error proxying to OpenAI: {e}")
        return HTTPException(status_code=500, detail=f"Error proxying to OpenAI: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    add_client(websocket)
    logger.info(f"✅ WebSocket client connected. Total clients: {len(clients)}")
    print(f"✅ WebSocket client connected. Total clients: {len(clients)}")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message["action"] == "stop":
                await stop_conversation()
            elif message["action"] == "start":
                selected_character = message["character"]
                await stop_conversation()  # Ensure any running conversation stops
                set_current_character(selected_character)
                await start_conversation()
            elif message["action"] == "set_character":
                set_current_character(message["character"])
                await websocket.send_json({"message": f"Character: {message['character']}"})
            elif message["action"] == "set_api_provider":
                # 全局API供应商开关：统一设置LLM、TTS、ASR
                set_env_variable("API_PROVIDER", message["provider"])
                await websocket.send_json({
                    "action": "api_provider_changed",
                    "provider": message["provider"],
                    "message": f"已切换到 {message['provider']} API供应商（LLM/TTS/ASR统一使用）"
                })
            elif message["action"] == "set_provider":
                # 已废弃：请使用set_api_provider
                set_env_variable("MODEL_PROVIDER", message["provider"])
            elif message["action"] == "set_tts":
                # 已废弃：请使用set_api_provider
                set_env_variable("TTS_PROVIDER", message["tts"])
            elif message["action"] == "set_asr":
                # 已废弃：请使用set_api_provider
                set_env_variable("ASR_PROVIDER", message["asr"])
            elif message["action"] == "set_openai_voice":
                set_env_variable("OPENAI_TTS_VOICE", message["voice"])
            elif message["action"] == "set_openai_model":
                set_env_variable("OPENAI_MODEL", message["model"])
            elif message["action"] == "set_ollama_model":
                set_env_variable("OLLAMA_MODEL", message["model"])
            elif message["action"] == "set_xai_model":
                set_env_variable("XAI_MODEL", message["model"])
            elif message["action"] == "set_anthropic_model":
                set_env_variable("ANTHROPIC_MODEL", message["model"])
            elif message["action"] == "set_voice_speed":
                set_env_variable("VOICE_SPEED", message["speed"])
            elif message["action"] == "set_elevenlabs_voice":
                set_env_variable("ELEVENLABS_TTS_VOICE", message["voice"])
            elif message["action"] == "set_kokoro_voice":
                set_env_variable("KOKORO_TTS_VOICE", message["voice"])
            elif message["action"] == "clear":
                conversation_history.clear()
                await websocket.send_json({"message": "Conversation history cleared."})
    except WebSocketDisconnect:
        remove_client(websocket)
        logger.info(f"Client disconnected from standard websocket")
    except Exception as e:
        logger.error(f"Error in standard websocket: {e}")
        # Still remove the client to prevent resource leaks
        remove_client(websocket)

@app.websocket("/ws_enhanced")
async def websocket_enhanced_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Add client to the list
    add_client(websocket)
    print(f"Enhanced WebSocket client {id(websocket)} connected")
    logging.info("connection open")
    
    # Notify client they are connected successfully
    try:
        await websocket.send_json({"action": "connected"})
    except:
        pass
    
    try:
        # Process messages from the client
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("action") == "ping":
                    # Respond to heartbeats
                    await websocket.send_json({"action": "pong"})
            except json.JSONDecodeError:
                # Not a JSON message
                pass
                
    except WebSocketDisconnect:
        logging.info("Client disconnected from enhanced websocket")
    except Exception as e:
        logging.error(f"Error in enhanced websocket: {e}")
    finally:
        # Remove client from the list on any error or disconnect
        remove_client(websocket)
        print(f"Enhanced WebSocket client {id(websocket)} disconnected")

# WebRTC OpenAI Realtime route (direct WebRTC implementation)
@app.get("/webrtc_realtime")
async def get_webrtc_realtime(request: Request):
    """
    Serves the WebRTC implementation of OpenAI Realtime API page.
    """
    try:
        # Get characters from characters folder
        characters = []
        if os.path.exists(characters_folder):
            characters = [d for d in os.listdir(characters_folder) 
                        if os.path.isdir(os.path.join(characters_folder, d))]
        
        # Provide a fallback if no characters found
        if not characters:
            characters = ["assistant"]
            logger.warning("No character folders found, using fallback assistant")
        
        # Get realtime model from environment variable or use default
        realtime_model = os.getenv("OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview-2024-12-17")
            
        return templates.TemplateResponse(
            "webrtc_realtime.html", 
            {
                "request": request,
                "characters": characters,
                "realtime_model": realtime_model,
            }
        )
    except Exception as e:
        logger.error(f"Error rendering WebRTC Realtime page: {e}")
        # Fallback with minimal context
        return templates.TemplateResponse(
            "webrtc_realtime.html", 
            {
                "request": request,
                "characters": ["assistant"],
                "realtime_model": "gpt-4o-realtime-preview-2024-12-17",  # Default fallback
            }
        )

@app.get("/api/character/{character_name}")
async def get_character_prompt(character_name: str):
    """
    Get the prompt for a specific character
    """
    try:
        prompt = load_character_prompt(character_name)
        return {"prompt": prompt}
    except Exception as e:
        logger.error(f"Error loading character prompt: {e}")
        return {"error": str(e)}

@app.get("/get_character_history")
async def get_character_history():
    """Get conversation history for currently selected character."""
    try:
        # Import with alias to avoid potential shadowing issues
        from .shared import get_current_character as get_character
        
        current_character = get_character()
        
        # Check if this is a story or game character
        is_story_character = current_character.startswith("story_") or current_character.startswith("game_")
        print(f"Getting history for {current_character} ({is_story_character=})")
        
        if is_story_character:
            # Get from character-specific history file
            character_dir = os.path.join(characters_folder, current_character)
            history_file = os.path.join(character_dir, "conversation_history.txt")
            
            if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_text = f.read()
                return {"status": "success", "history": history_text, "character": current_character}
            else:
                return {"status": "empty", "history": "", "character": current_character}
        else:
            # For non-story characters, return empty history
            return {"status": "not_story_character", "history": "", "character": current_character}
    except Exception as e:
        print(f"Error getting character history: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/voice/upload")
async def upload_voice_audio(
    audio: UploadFile = File(...),
    character: str = Form("english_tutor")
):
    """处理上传的语音文件"""
    try:
        from .transcription import transcribe_with_openai_api
        import tempfile
        import os
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # 转录音频 - 需要将webm转换为wav格式
        audio_converted = False
        try:
            from pydub import AudioSegment
            # 将webm转换为wav
            audio_seg = AudioSegment.from_file(tmp_file_path, format="webm")
            wav_path = tmp_file_path.replace('.webm', '.wav')
            audio_seg.export(wav_path, format="wav")
            # 清理原始webm文件
            os.unlink(tmp_file_path)
            tmp_file_path = wav_path
            audio_converted = True
            logger.info("Audio converted from webm to wav successfully")
        except ImportError as e:
            logger.warning(f"pydub not available, trying to use original file: {e}")
            # pydub未安装，尝试直接使用原文件
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 如果转换失败，尝试直接使用原文件
            if not tmp_file_path.endswith('.wav'):
                logger.warning("Audio conversion failed, but will try to use original file format")
        
        # 转录音频
        transcription = None
        try:
            transcription = await transcribe_with_openai_api(tmp_file_path)
            if not transcription or transcription.strip() == "":
                raise ValueError("Transcription returned empty result")
            logger.info(f"Transcription successful: {transcription[:50]}...")
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 如果转换失败且文件不是wav格式，尝试重新转换
            if not audio_converted and not tmp_file_path.endswith('.wav'):
                logger.info("Retrying with alternative conversion method...")
                try:
                    # 尝试使用ffmpeg直接转换（如果可用）
                    import subprocess
                    wav_path = tmp_file_path.replace('.webm', '.wav').replace('.mp3', '.wav')
                    subprocess.run(['ffmpeg', '-i', tmp_file_path, '-y', wav_path], 
                                 check=True, capture_output=True)
                    os.unlink(tmp_file_path)
                    tmp_file_path = wav_path
                    transcription = await transcribe_with_openai_api(tmp_file_path)
                    if not transcription or transcription.strip() == "":
                        raise ValueError("Transcription returned empty result")
                    logger.info(f"Transcription successful after ffmpeg conversion: {transcription[:50]}...")
                except Exception as e2:
                    logger.error(f"Alternative conversion also failed: {e2}")
                    raise e  # 抛出原始错误
            else:
                raise
        
        # 清理临时文件
        try:
            os.unlink(tmp_file_path)
        except:
            pass
        
        # 设置角色
        set_current_character(character)
        
        # 首次使用时加载记忆和历史
        from .shared import conversation_history, get_memory_system
        if len(conversation_history) == 0:
            # 加载完整对话历史（最近50条）
            from .app_logic import load_character_specific_history
            is_story_character = character.startswith("story_") or character.startswith("game_")
            if is_story_character:
                loaded_history = load_character_specific_history(character)
                if loaded_history:
                    # 只加载最近50条
                    conversation_history.extend(loaded_history[-50:])
                    logger.info(f"Loaded {len(loaded_history[-50:])} messages from character-specific history")
            # 不再加载全局历史文件（conversation_history.txt 已移除）
        
        # 发送用户消息到客户端（只发送一次）
        from .app import send_message_to_clients
        await send_message_to_clients(json.dumps({
            "action": "user_message",
            "text": transcription
        }))
        
        # 将用户输入添加到对话历史
        conversation_history.append({"role": "user", "content": transcription})
        
        # 处理用户输入并生成回复（在后台任务中执行，避免阻塞）
        from .app_logic import process_text
        asyncio.create_task(process_text(transcription))
        
        return JSONResponse({
            "status": "success",
            "transcription": transcription
        })
        
    except Exception as e:
        logger.error(f"Error processing voice upload: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"处理语音失败: {str(e)}"
        }, status_code=500)

@app.post("/api/text/send")
async def send_text_message(request: Request):
    """处理文字消息"""
    try:
        data = await request.json()
        text = data.get("text", "").strip()
        character = data.get("character", "english_tutor")
        
        if not text:
            return JSONResponse({
                "status": "error",
                "message": "消息内容不能为空"
            }, status_code=400)
        
        # 场景 NPC 角色（cafe_waiter 等）若不存在则回退到 english_tutor
        characters_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "characters")
        char_path = os.path.join(characters_dir, character)
        if not os.path.isdir(char_path) or not os.path.exists(os.path.join(char_path, f"{character}.txt")):
            character = "english_tutor"
        set_current_character(character)
        
        # 首次使用时加载记忆和历史
        from .shared import conversation_history, get_memory_system
        if len(conversation_history) == 0:
            # 加载完整对话历史（最近50条）
            from .app_logic import load_character_specific_history
            is_story_character = character.startswith("story_") or character.startswith("game_")
            if is_story_character:
                loaded_history = load_character_specific_history(character)
                if loaded_history:
                    # 只加载最近50条
                    conversation_history.extend(loaded_history[-50:])
                    logger.info(f"Loaded {len(loaded_history[-50:])} messages from character-specific history")
            # 不再加载全局历史文件（conversation_history.txt 已移除）
        
        # 发送用户消息到客户端
        from .app import send_message_to_clients
        await send_message_to_clients(json.dumps({
            "action": "user_message",
            "text": text
        }))
        
        # 将用户输入添加到对话历史
        conversation_history.append({"role": "user", "content": text})
        
        # 处理用户输入并生成回复（在后台任务中执行，避免阻塞）
        from .app_logic import process_text
        asyncio.create_task(process_text(text))
        
        return JSONResponse({
            "status": "success",
            "message": "消息已发送"
        })
        
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"处理消息失败: {str(e)}"
        }, status_code=500)

@app.post("/api/conversation/end")
async def end_conversation(request: Request):
    """结束对话并生成摘要，如果处于中文沟通阶段则提示可以生成英文对话"""
    try:
        from .shared import get_memory_system, get_current_character, get_learning_stage, get_current_account
        
        memory_system = get_memory_system()
        if not memory_system:
            return JSONResponse({
                "status": "error",
                "message": "记忆系统未初始化"
            }, status_code=500)
        
        current_character = get_current_character()
        learning_stage = get_learning_stage()
        
        # 从会话中提取用户信息（不再生成或保存 diary）
        session_data = memory_system.load_session_temp()
        if session_data and session_data.get("messages"):
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in session_data["messages"]
            ])
            extracted_info = await memory_system.extract_user_info(conversation_text)
        
        # 清空临时会话文件
        memory_system.clear_session_temp()
        
        # 场景-NPC：大场景→小场景→NPC
        from .scene_npc_db import get_big_scenes
        account_name = get_current_account() or ""
        big_scenes = get_big_scenes()
        
        response_data = {
            "status": "success",
            "message": "对话已结束，记忆已保存。请选择场景后生成英语卡片",
            "summary": "",
            "timestamp": "",
            "should_generate_english": True,
            "big_scenes": big_scenes,
        }
        return JSONResponse(response_data)
            
    except Exception as e:
        logger.error(f"Error ending conversation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"结束对话时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/english/generate")
async def generate_english_dialogue(request: Request):
    """生成英文教学对话（从 dialogues.json 取 learn 对话，含 TTS 音频）"""
    try:
        from .shared import set_learning_stage
        from .scene_npc_db import get_learn_dialogue, build_card_title

        data = await request.json()
        small_scene_id = (data.get("small_scene_id") or data.get("scene") or "").strip()
        npc_id = (data.get("npc_id") or "").strip()

        if not small_scene_id or not npc_id:
            return JSONResponse({
                "status": "error",
                "message": "请提供 small_scene_id 与 npc_id"
            }, status_code=400)

        dialogue = get_learn_dialogue(small_scene_id, npc_id)
        if not dialogue:
            return JSONResponse({
                "status": "error",
                "message": "未找到该场景的对话内容"
            }, status_code=404)

        content = dialogue.get("content", [])
        dialogue_parts = []
        dialogue_lines = []
        for item in content:
            role = item.get("role", "B")
            text = item.get("content", "")
            hint = item.get("hint", "")
            dialogue_parts.append(f"{role}: {text}")
            dialogue_lines.append({"speaker": role, "text": text, "hint": hint, "audio_url": None})

        dialogue_id = dialogue.get("dialogue_id", f"{small_scene_id}-{npc_id}-learn")
        from .memory_system import generate_tts_for_dialogue_lines
        await generate_tts_for_dialogue_lines(dialogue_lines, dialogue_id)

        dialogue_text = "\n".join(dialogue_parts)
        card_title = build_card_title(dialogue)
        set_learning_stage("english_learning")
        return JSONResponse({
            "status": "success",
            "message": "英文对话已生成",
            "dialogue": dialogue_text,
            "dialogue_lines": dialogue_lines,
            "dialogue_id": dialogue_id,
            "small_scene_id": small_scene_id,
            "npc_id": npc_id,
            "npc_name": dialogue.get("npc_name", "").strip() or npc_id,
            "card_title": card_title,
        })

    except Exception as e:
        logger.error(f"Error generating english dialogue: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"生成英文对话时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/learning/recommend")
async def api_learning_recommend(request: Request):
    """获取学习推荐：优先从对话摘要推断 1 个主题+场景，否则从练习记忆；其余随机。返回带 title 的推荐列表。"""
    try:
        from .shared import get_current_account
        from .scene_npc_db import get_learning_recommendations

        account_name = get_current_account() or ""
        try:
            body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        except Exception:
            body = {}
        conversation_summary = (body.get("conversation_summary") or "").strip() or None
        count = max(1, min(10, int(body.get("count", 4))))

        recommendations = get_learning_recommendations(account_name, conversation_summary, count=count)
        return JSONResponse({"recommendations": recommendations})
    except Exception as e:
        logger.error(f"Error in learning recommend: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({"recommendations": [], "error": str(e)}, status_code=500)


@app.post("/api/learning/start_english")
async def start_english_learning(request: Request):
    """手动切换到英文学习阶段"""
    try:
        from .shared import set_learning_stage, get_learning_stage

        current_stage = get_learning_stage()
        if current_stage == "english_learning":
            return JSONResponse({
                "status": "info",
                "message": "已经处于英文学习阶段"
            })
        
        set_learning_stage("english_learning")
        
        return JSONResponse({
            "status": "success",
            "message": "已切换到英文学习阶段，现在AI会用英文回复你"
        })
    except Exception as e:
        logger.error(f"Error starting english learning: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"切换失败: {str(e)}"
        }, status_code=500)

@app.post("/api/user/update_english_level")
async def update_english_level(request: Request):
    """更新用户英文水平"""
    try:
        from .shared import get_memory_system
        
        data = await request.json()
        level = data.get("level", "beginner")
        description = data.get("description", "")
        
        memory_system = get_memory_system()
        if not memory_system:
            return JSONResponse({
                "status": "error",
                "message": "记忆系统未初始化"
            }, status_code=500)
        
        memory_system.update_english_level(level, description)
        
        return JSONResponse({
            "status": "success",
            "message": "英文水平已更新",
            "level": level
        })
    except Exception as e:
        logger.error(f"Error updating english level: {e}")
        return JSONResponse({
            "status": "error",
            "message": f"更新英文水平时出错: {str(e)}"
        }, status_code=500)

# 练习模式会话存储（临时存储，练习完成后保存到文件）
practice_sessions = {}  # {session_id: {user_inputs: [], dialogue_lines: [], dialogue_topic: ""}}

# 练习模式相关API
@app.post("/api/practice/start")
async def start_practice(request: Request):
    """开始练习阶段，解析对话卡片并初始化状态。
    耗时主要来自：若无音频则整段 TTS。前端会显示「正在准备练习资料」提示。"""
    try:
        from .shared import get_memory_system
        from .app import chatgpt_streamed_async
        import asyncio
        import uuid
        
        data = await request.json()
        dialogue = data.get("dialogue", "").strip()
        dialogue_lines_from_card = data.get("dialogue_lines", [])  # 从英语卡片获取的对话行（包含音频URL）
        dialogue_id_from_card = data.get("dialogue_id", "")  # 从英语卡片获取的对话ID
        small_scene_id = (data.get("small_scene_id") or "").strip()
        npc_id = (data.get("npc_id") or "").strip()
        
        if not dialogue:
            return JSONResponse({
                "status": "error",
                "message": "对话内容不能为空"
            }, status_code=400)
        
        # 如果从卡片获取了对话行数据，直接使用（包含音频URL）
        # 否则解析对话文本（兼容旧格式）
        dialogue_lines = []
        if dialogue_lines_from_card and len(dialogue_lines_from_card) > 0:
            # 使用卡片提供的对话行数据（包含音频URL）
            dialogue_lines = dialogue_lines_from_card
        else:
            # 解析对话文本（兼容旧格式，没有音频URL）
            lines = dialogue.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('A:'):
                    content = line[2:].strip()
                    if content:
                        dialogue_lines.append({"speaker": "A", "text": content, "audio_url": None})
                elif line.startswith('B:'):
                    content = line[2:].strip()
                    if content:
                        dialogue_lines.append({"speaker": "B", "text": content, "audio_url": None})
        
        if not dialogue_lines:
            return JSONResponse({
                "status": "error",
                "message": "无法解析对话内容"
            }, status_code=400)
        
        # 若有场景与 NPC，从数据库补全每条行的 hint（前端可能漏传，导致提示变成原句）
        if small_scene_id and npc_id:
            try:
                from .scene_npc_db import get_learn_dialogue, get_immersive_dialogue
                db_dialogue = get_immersive_dialogue(small_scene_id, npc_id) or get_learn_dialogue(small_scene_id, npc_id)
                if db_dialogue and db_dialogue.get("content"):
                    content = db_dialogue["content"]
                    for i, line in enumerate(dialogue_lines):
                        if i < len(content):
                            item = content[i]
                            role = item.get("role", "B")
                            if line.get("speaker") == role and line.get("text") == item.get("content", ""):
                                line["hint"] = item.get("hint", "")
            except Exception as e:
                logger.warning("补全 dialogue_lines hint 失败: %s", e)
        
        # 规则：A=NPC（对方），B=用户（学习者）。允许以A或B开始
        if dialogue_lines[0]["speaker"] not in ("A", "B"):
            return JSONResponse({
                "status": "error",
                "message": "对话角色必须为A（NPC）或B（用户）"
            }, status_code=400)
        
        # 使用卡片提供的对话ID，或生成新的
        dialogue_id = dialogue_id_from_card if dialogue_id_from_card else f"practice_{int(datetime.now().timestamp() * 1000)}"
        
        # 生成会话ID用于跟踪练习会话
        session_id = str(uuid.uuid4())
        
        # 对话主题固定为「日常对话」，供生成复习笔记时 prompt 使用（不再用 LLM 分析）
        dialogue_topic = "日常对话"
        
        # 若对话行无音频（如来自场景沉浸式），则生成 TTS
        needs_tts = any(
            line.get("speaker") == "A" and not line.get("audio_url")
            for line in dialogue_lines
        )
        if needs_tts:
            try:
                from .memory_system import generate_tts_for_dialogue_lines
                tts_id = (dialogue_id or f"scene_{small_scene_id}_{npc_id}").replace("/", "_")
                await generate_tts_for_dialogue_lines(dialogue_lines, tts_id)
            except Exception as e:
                logger.warning(f"场景对话 TTS 生成失败: {e}")
        
        # 初始化练习会话记录
        practice_sessions[session_id] = {
            "dialogue_id": dialogue_id,
            "dialogue_lines": dialogue_lines,
            "user_inputs": [],
            "dialogue_topic": dialogue_topic,
            "start_time": datetime.now().isoformat(),
            "small_scene_id": small_scene_id,
            "npc_id": npc_id,
        }
        
        # 获取第一句台词。规则：A=NPC，B=用户。可能以A或B开始
        first_a_text = None
        first_a_audio_url = None
        first_b_text = None
        first_b_line = {}
        if dialogue_lines[0]["speaker"] == "A":
            first_a_text = dialogue_lines[0]["text"]
            first_a_audio_url = dialogue_lines[0].get("audio_url")
            if len(dialogue_lines) > 1 and dialogue_lines[1]["speaker"] == "B":
                first_b_text = dialogue_lines[1]["text"]
                first_b_line = dialogue_lines[1]
        else:
            # 以B开始：用户先说第一句
            first_b_text = dialogue_lines[0]["text"]
            first_b_line = dialogue_lines[0]
        
        # 如果有B的台词，取提示：优先用口语库的 hint（须含关键词/关键句），否则 AI 抽取
        hints = None
        if first_b_text:
            if first_b_line.get("hint"):
                h = first_b_line["hint"]
                phrases = [x.strip() for x in h.split("/") if x.strip()]
                # 若 hint 像动作描述（如 ask address）无具体可说内容，用本句 content 作参考句
                if len(phrases) == 1 and phrases[0].islower() and "?" not in phrases[0] and len(phrases[0]) < 30:
                    phrases.append(first_b_text)
                hints = {"phrases": phrases, "pattern": "", "words": [], "grammar": "", "key_sentence": first_b_text}
            else:
                hints = {"phrases": [first_b_text], "pattern": "", "words": [], "grammar": "", "key_sentence": first_b_text}
        
        return JSONResponse({
            "status": "success",
            "session_id": session_id,  # 返回会话ID，前端需要保存
            "dialogue_id": dialogue_id,
            "dialogue_lines": dialogue_lines,
            "current_turn": 0,
            "a_text": first_a_text,
            "a_audio_url": first_a_audio_url,  # 返回第一句A的音频URL
            "b_hints": hints,
            "total_turns": len([l for l in dialogue_lines if l["speaker"] == "B"])
        })
        
    except Exception as e:
        logger.error(f"Error starting practice: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"开始练习时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/practice/respond")
async def practice_respond(request: Request):
    """用户回复，验证意思一致性"""
    try:
        from .shared import get_memory_system
        from .app import chatgpt_streamed_async
        import asyncio
        
        data = await request.json()
        user_input = data.get("user_input", "").strip()
        dialogue_lines = data.get("dialogue_lines", [])
        current_turn = data.get("current_turn", 0)
        session_id = data.get("session_id", "")  # 获取会话ID
        
        if not user_input:
            return JSONResponse({
                "status": "error",
                "message": "用户输入不能为空"
            }, status_code=400)
        
        # 找到当前轮次对应的B的参考台词
        b_turn_index = 0
        reference_text = None
        for i, line in enumerate(dialogue_lines):
            if line["speaker"] == "B":
                if b_turn_index == current_turn:
                    reference_text = line["text"]
                    break
                b_turn_index += 1
        else:
            return JSONResponse({
                "status": "error",
                "message": "找不到对应的参考台词"
            }, status_code=400)
        
        # 记录对话上下文（AI说的和用户说的）到会话数据中
        if session_id and session_id in practice_sessions:
            # 找到当前轮次对应的A的台词（AI说的，作为上下文）
            ai_said = None
            for i, line in enumerate(dialogue_lines):
                if line["speaker"] == "A":
                    # 检查这个A后面是否有对应的B（当前轮次）
                    b_count = 0
                    for j in range(i + 1, len(dialogue_lines)):
                        if dialogue_lines[j]["speaker"] == "B":
                            if b_count == current_turn:
                                ai_said = line["text"]
                                break
                            b_count += 1
                        elif dialogue_lines[j]["speaker"] == "A":
                            # 如果遇到下一个A，说明当前A不是我们要找的
                            break
                    if ai_said:
                        break
            
            practice_sessions[session_id]["user_inputs"].append({
                "turn": current_turn,
                "ai_said": ai_said or "",  # AI说的话（上下文）
                "user_said": user_input,    # 用户说的话
                "timestamp": datetime.now().isoformat()
            })
        
        # 验证意思一致性
        validation_result = await check_meaning_consistency(user_input, reference_text)
        
        # 如果意思一致，获取下一句A的台词
        next_a_text = None
        next_a_audio_url = None
        next_b_hints = None
        next_turn = current_turn + 1
        is_completed = False  # 初始化 is_completed
        
        if validation_result.get("result") in ["consistent", "consistent_with_errors"]:
            # 找到当前B之后的下一个A的台词
            b_count = 0
            found_current_b = False
            
            for i, line in enumerate(dialogue_lines):
                if line["speaker"] == "B":
                    if b_count == current_turn:
                        found_current_b = True
                        # 找到当前B，往后找下一个A
                        for j in range(i + 1, len(dialogue_lines)):
                            if dialogue_lines[j]["speaker"] == "A":
                                next_a_text = dialogue_lines[j]["text"]
                                next_a_audio_url = dialogue_lines[j].get("audio_url")  # 获取下一句A的音频URL
                                # 如果A后面还有B，取提示：优先用口语库的 hint，否则 AI 抽取
                                if j + 1 < len(dialogue_lines) and dialogue_lines[j + 1]["speaker"] == "B":
                                    next_b_line = dialogue_lines[j + 1]
                                    if next_b_line.get("hint"):
                                        h = next_b_line["hint"]
                                        phrases = [x.strip() for x in h.split("/") if x.strip()]
                                        ref_text = next_b_line.get("text", "")
                                        if len(phrases) == 1 and phrases[0].islower() and "?" not in phrases[0] and len(phrases[0]) < 30 and ref_text:
                                            phrases.append(ref_text)
                                        next_b_hints = {"phrases": phrases, "pattern": "", "words": [], "grammar": "", "key_sentence": ref_text}
                                    else:
                                        ref_text = next_b_line.get("text", "")
                                        next_b_hints = {"phrases": [ref_text] if ref_text else [], "pattern": "", "words": [], "grammar": "", "key_sentence": ref_text}
                                    is_completed = False  # 还有下一轮，未完成
                                else:
                                    is_completed = True
                                break
                        break
                    b_count += 1
            
            # 如果找不到下一个A，说明对话已完成
            if next_a_text is None:
                is_completed = True
        else:
            is_completed = False
        
        return JSONResponse({
            "status": "success",
            "is_consistent": validation_result.get("result") in ["consistent", "consistent_with_errors"],
            "validation_result": validation_result,
            "next_a_text": next_a_text,
            "next_a_audio_url": next_a_audio_url,  # 返回下一句A的音频URL
            "next_b_hints": next_b_hints,
            "next_turn": next_turn if next_a_text else current_turn,
            "is_completed": is_completed,
            "session_id": session_id  # 返回会话ID，前端需要保存
        })
        
    except Exception as e:
        logger.error(f"Error in practice respond: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"处理回复时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/practice/end")
async def end_practice(request: Request):
    """结束练习，返回完整的练习会话数据"""
    try:
        
        data = await request.json()
        session_id = data.get("session_id", "")
        
        if not session_id:
            return JSONResponse({
                "status": "error",
                "message": "会话ID不能为空"
            }, status_code=400)
        
        if session_id not in practice_sessions:
            return JSONResponse({
                "status": "error",
                "message": "找不到对应的练习会话"
            }, status_code=404)
        
        # 获取会话数据，直接返回（不再调用 LLM 提取主题，使用开始练习时已有的 dialogue_topic）
        session_data = practice_sessions[session_id].copy()
        session_data["end_time"] = datetime.now().isoformat()
        
        return JSONResponse({
            "status": "success",
            "session_data": session_data
        })
        
    except Exception as e:
        logger.error(f"Error ending practice: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"结束练习时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/practice/generate-review")
async def generate_review_notes(request: Request):
    """生成复习笔记。三部分：1) AI 纠错 2) 核心句型与语块（来自 DB 对应 Review）3) Review 短对话（来自 DB 对应 Review）"""
    try:
        from .app import chatgpt_streamed_async
        import json

        data = await request.json()
        user_inputs = data.get("user_inputs", [])
        dialogue_topic = data.get("dialogue_topic", "日常对话")
        dialogue_id = data.get("dialogue_id", "")
        small_scene_id = (data.get("small_scene_id") or "").strip()
        npc_id = (data.get("npc_id") or "").strip()

        if not user_inputs:
            return JSONResponse({
                "status": "error",
                "message": "用户输入数据不能为空"
            }, status_code=400)

        # 第一部分：仅让 AI 生成纠错
        user_inputs_text = "\n".join([
            f"轮次 {item['turn']}:\n  AI说: {item.get('ai_said', '')}\n  用户说: {item.get('user_said', '')}"
            for item in user_inputs
        ])
        prompt = f"""基于以下练习会话，仅对用户说的内容进行纠错，输出 JSON。

【重要】用户输入来自语音转写（ASR），不要纠书写类错误（大小写、标点、拼写等），只从口语角度纠错：
- 纠发音导致的用词错误（如 homophone 听写错）
- 纠语法错误（时态、主谓一致、词序等）
- 纠表达不当或不符合口语习惯的用法
- 忽略：大小写、句号逗号、标点符号、拼写变体（如 gonna vs going to）

对话主题：{dialogue_topic}

会话内容：
{user_inputs_text}

请只输出如下 JSON（不要其他文字）：
{{
  "corrections": [
    {{
      "user_said": "用户说的原句",
      "correct": "正确表达",
      "explanation": "简要纠错说明（侧重发音或语法）"
    }}
  ]
}}

要求：只对有明显发音或语法错误的句子给出纠错；若某句没问题可省略。只返回 JSON。
"""

        response = await chatgpt_streamed_async(
            prompt,
            "你是英语口语纠错助手。用户输入来自语音转写，只纠发音和语法错误，不纠书写、标点、大小写。",
            "neutral",
            []
        )

        if not response or not response.strip():
            return JSONResponse({
                "status": "error",
                "message": "AI生成失败，返回空响应"
            }, status_code=500)

        try:
            response_text = response.strip()
            # 去掉 markdown 代码块包裹（如 ```json ... ```）
            if "```" in response_text:
                start_marker = "```json" if "```json" in response_text else "```"
                start = response_text.find(start_marker) + len(start_marker)
                end = response_text.find("```", start)
                if end > start:
                    response_text = response_text[start:end].strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                ai_part = json.loads(response_text[json_start:json_end])
            else:
                ai_part = {"corrections": []}
        except json.JSONDecodeError as e:
            logger.warning(f"generate_review: AI 返回非合法 JSON, {e}, 原始片段: {(response or '')[:200]}")
            ai_part = {"corrections": []}

        raw_list = ai_part.get("corrections") or []
        # 统一为 { user_said, correct, explanation }，兼容 LLM 用不同 key 的情况
        corrections = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            user_said = item.get("user_said") or item.get("original") or item.get("user_input") or ""
            correct = item.get("correct") or item.get("corrected") or item.get("suggestion") or ""
            if user_said or correct:
                corrections.append({
                    "user_said": user_said,
                    "correct": correct,
                    "explanation": item.get("explanation") or item.get("reason") or ""
                })

        # 第二、三部分：从 scene_npc 的 review 对话取核心句型、语块与短对话
        core_sentences = ""
        core_chunks = ""
        review_dialogue = []
        if small_scene_id and npc_id:
            try:
                from .scene_npc_db import get_review_dialogue
                rev = get_review_dialogue(small_scene_id, npc_id)
                if rev:
                    core_sentences = rev.get("core_sentences", "") or ""
                    core_chunks = rev.get("core_chunks", "") or ""
                    for item in rev.get("content", []):
                        review_dialogue.append({
                            "speaker": item.get("role", "A"),
                            "text": item.get("content", ""),
                            "hint": item.get("hint", ""),
                            "audio_url": None
                        })
            except Exception as e:
                logger.warning(f"Scene NPC review failed: {e}")
        elif dialogue_id:
            try:
                from . import oral_training_db as otd
                rec = otd.get_record_by_dialogue_id(dialogue_id)
                if rec:
                    review_row = otd.get_review_record(rec.get("scene", ""), rec.get("unit", ""))
                    if review_row:
                        core_sentences = review_row.get("core_sentences", "") or ""
                        core_chunks = review_row.get("core_chunks", "") or ""
                        if review_row.get("content"):
                            review_dialogue = [
                                {"speaker": item.get("role", "A"), "text": item.get("content", ""), "hint": item.get("hint", ""), "audio_url": None}
                                for item in review_row["content"]
                            ]
            except Exception as e:
                logger.warning(f"Oral DB review attachment failed: {e}")

        # 为复习对话生成 TTS 音频
        if review_dialogue:
            from .memory_system import generate_tts_for_dialogue_lines
            review_audio_id = f"review_{(small_scene_id or npc_id or dialogue_id or 'x').replace('/', '_')}_{uuid.uuid4().hex[:8]}"
            await generate_tts_for_dialogue_lines(review_dialogue, review_audio_id)

        review_notes = {
            "corrections": corrections,
            "core_sentences": core_sentences,
            "core_chunks": core_chunks,
            "review_dialogue": review_dialogue,
        }

        return JSONResponse({
            "status": "success",
            "review_notes": review_notes
        })
        
    except Exception as e:
        logger.error(f"Error generating review notes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"生成复习笔记时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/knowledge/select-scene")
async def select_scene(request: Request):
    """用户选择场景（与难度），记录到 scene_choices（口语训练库）"""
    try:
        from .shared import get_current_account
        from . import oral_training_db as otd
        
        data = await request.json()
        scene = (data.get("scene") or data.get("scene_primary") or "").strip()
        difficulty = (data.get("difficulty") or data.get("difficulty_level") or "").strip()
        
        account_name = get_current_account()
        if not account_name:
            return JSONResponse({
                "status": "error",
                "message": "用户未登录"
            }, status_code=401)
        
        if not scene:
            return JSONResponse({
                "status": "error",
                "message": "请提供 scene（场景）"
            }, status_code=400)
        
        otd.increment_scene_choice(account_name, scene)
        return JSONResponse({
            "status": "success",
            "message": "场景选择已记录",
            "scene": scene,
            "difficulty": difficulty or None,
        })
        
    except Exception as e:
        logger.error(f"Error selecting scene: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"选择场景时出错: {str(e)}"
        }, status_code=500)

@app.get("/api/knowledge/available-scenes")
async def get_available_scenes():
    """获取可选场景（recommended + frequent + new）与难度列表，基于口语训练库"""
    try:
        from .shared import get_current_account
        from . import oral_training_db as otd
        account_name = get_current_account() or ""
        scene_options = otd.get_scene_options_for_user(account_name, None)
        return JSONResponse({
            "status": "success",
            "suggested_scene": scene_options.get("suggested_scene"),
            "available_scenes": scene_options.get("options", []),
            "available_difficulties": otd.get_unique_difficulties(),
        })
    except Exception as e:
        logger.error(f"Error getting available scenes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": str(e),
            "available_scenes": [],
            "available_difficulties": [],
        }, status_code=500)

@app.get("/api/knowledge/recommended")
async def get_recommended_knowledge(request: Request):
    """获取推荐知识点"""
    try:
        from .shared import get_memory_system, get_current_account
        from .knowledge_db import KnowledgeDatabase
        
        account_name = get_current_account()
        if not account_name:
            return JSONResponse({
                "status": "error",
                "message": "用户未登录"
            }, status_code=401)
        
        # 获取用户水平
        memory_system = get_memory_system()
        user_level = "beginner"
        if memory_system:
            user_level = memory_system.user_profile.get("english_level", "beginner")
        
        # 获取场景参数（可选）：label_id 或 scene_primary + scene_secondary
        selected_label_id = request.query_params.get("label_id") or request.query_params.get("selected_label_id")
        scene_primary = request.query_params.get("scene_primary")
        scene_secondary = request.query_params.get("scene_secondary")
        if selected_label_id is not None:
            try:
                selected_label_id = int(selected_label_id)
            except (TypeError, ValueError):
                selected_label_id = None
        
        kb = KnowledgeDatabase()
        recommended = kb.get_recommended_knowledge(
            user_id=account_name,
            user_level=user_level,
            selected_label_id=selected_label_id,
            scene_primary=scene_primary,
            scene_secondary=scene_secondary,
        )
        
        return JSONResponse({
            "status": "success",
            "recommended": recommended,
            "count": len(recommended)
        })
        
    except Exception as e:
        logger.error(f"Error getting recommended knowledge: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"获取推荐知识点时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/practice/save-memory")
async def save_practice_memory(request: Request):
    """保存练习记忆到文件"""
    try:
        from .shared import get_memory_system
        from .scene_npc_db import mark_npc_learned, check_and_unlock_scene
        
        data = await request.json()
        small_scene_id = (data.get("small_scene_id") or "").strip()
        npc_id = (data.get("npc_id") or "").strip()
        if small_scene_id and npc_id:
            account_name = get_current_account() or ""
            if account_name:
                mark_npc_learned(account_name, small_scene_id, npc_id)
                check_and_unlock_scene(account_name, small_scene_id)
        
        memory_system = get_memory_system()
        
        if not memory_system:
            return JSONResponse({
                "status": "error",
                "message": "记忆系统未初始化"
            }, status_code=500)
        
        # 保存练习记忆
        success = memory_system.save_practice_memory(data)
        
        if success:
            return JSONResponse({
                "status": "success",
                "message": "练习记忆已保存"
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": "保存练习记忆失败"
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"Error saving practice memory: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"保存练习记忆时出错: {str(e)}"
        }, status_code=500)


@app.post("/api/practice/mark-unit-mastered")
async def mark_unit_mastered_api(request: Request):
    """用户自评「掌握了」时调用。支持两种来源：
    1) 口语训练库：dialogue_id → oral_training_db.mark_unit_mastered
    2) 场景 NPC：small_scene_id + npc_id → scene_npc_db.mark_npc_learned（记录为已学会）
    """
    try:
        from .shared import get_current_account
        from . import oral_training_db as otd
        from .scene_npc_db import mark_npc_learned, check_and_unlock_scene

        account_name = get_current_account() or ""
        if not account_name:
            return JSONResponse({
                "status": "error",
                "message": "请先登录账户"
            }, status_code=401)
        data = await request.json()
        dialogue_id = (data.get("dialogue_id") or "").strip()
        small_scene_id = (data.get("small_scene_id") or "").strip()
        npc_id = (data.get("npc_id") or "").strip()

        # 优先处理场景 NPC 来源（复习资料来自大场景→小场景→NPC 流程）
        if small_scene_id and npc_id:
            mark_npc_learned(account_name, small_scene_id, npc_id)
            check_and_unlock_scene(account_name, small_scene_id)
            return JSONResponse({
                "status": "success",
                "message": "已标记为已掌握，下次选择时将显示已完成"
            })

        # 口语训练库来源
        if not dialogue_id:
            return JSONResponse({
                "status": "error",
                "message": "缺少 dialogue_id 或 small_scene_id + npc_id"
            }, status_code=400)
        rec = otd.get_record_by_dialogue_id(dialogue_id)
        if not rec:
            return JSONResponse({
                "status": "error",
                "message": "未找到对应练习记录"
            }, status_code=404)
        scene = rec.get("scene") or ""
        unit = rec.get("unit") or ""
        if not scene or not unit:
            return JSONResponse({
                "status": "error",
                "message": "记录缺少 scene 或 unit"
            }, status_code=400)
        otd.mark_unit_mastered(account_name, scene, unit)
        return JSONResponse({
            "status": "success",
            "message": "已标记为本单元已掌握，下次将不再推荐该单元的后续批次"
        })
    except Exception as e:
        logger.error(f"Error marking unit mastered: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"标记失败: {str(e)}"
        }, status_code=500)

@app.post("/api/practice/transcribe")
async def practice_transcribe_audio(
    audio: UploadFile = File(...)
):
    """练习模式下只转录音频，不生成AI回复（避免token浪费）"""
    try:
        from .transcription import transcribe_with_openai_api
        import tempfile
        import os
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # 转录音频 - 需要将webm转换为wav格式
        audio_converted = False
        try:
            from pydub import AudioSegment
            # 将webm转换为wav
            audio_seg = AudioSegment.from_file(tmp_file_path, format="webm")
            wav_path = tmp_file_path.replace('.webm', '.wav')
            audio_seg.export(wav_path, format="wav")
            tmp_file_path = wav_path
            audio_converted = True
        except Exception as e:
            logger.warning(f"Could not convert audio format: {e}")
            # 如果转换失败，尝试直接使用原文件
        
        # 转录音频
        transcription = None
        try:
            transcription = await transcribe_with_openai_api(tmp_file_path, "gpt-4o-mini-transcribe")
            if not transcription or transcription.strip() == "":
                raise ValueError("Transcription returned empty result")
            logger.info(f"Practice transcription successful: {transcription[:50]}...")
        except Exception as e:
            logger.error(f"Error during practice transcription: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 清理临时文件
            try:
                os.unlink(tmp_file_path)
                if audio_converted and os.path.exists(tmp_file_path.replace('.wav', '.webm')):
                    os.unlink(tmp_file_path.replace('.wav', '.webm'))
            except:
                pass
            return JSONResponse({
                "status": "error",
                "message": f"转录音频失败: {str(e)}"
            }, status_code=500)
        
        # 保存用户音频文件（用于音频气泡显示）
        audio_url = None
        try:
            import uuid
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(current_file_dir)
            practice_audio_dir = os.path.join(project_dir, "outputs", "practice")
            os.makedirs(practice_audio_dir, exist_ok=True)
            
            # 生成唯一的音频文件名
            audio_filename = f"user_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp() * 1000)}.wav"
            saved_audio_path = os.path.join(practice_audio_dir, audio_filename)
            
            # 复制音频文件到保存目录
            shutil.copy2(tmp_file_path, saved_audio_path)
            
            # 生成音频URL
            audio_url = f"/audio/practice/{audio_filename}"
            logger.info(f"User audio saved: {audio_url}")
        except Exception as e:
            logger.error(f"Error saving user audio: {e}")
            # 即使保存失败，也继续返回转录结果
        
        # 清理临时文件
        try:
            os.unlink(tmp_file_path)
            if audio_converted and os.path.exists(tmp_file_path.replace('.wav', '.webm')):
                os.unlink(tmp_file_path.replace('.wav', '.webm'))
        except:
            pass
        
        return JSONResponse({
            "status": "success",
            "transcription": transcription,
            "audio_url": audio_url  # 返回音频URL
        })
        
    except Exception as e:
        logger.error(f"Error transcribing audio for practice: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"转录音频失败: {str(e)}"
        }, status_code=500)

# 辅助函数
async def check_meaning_consistency(user_input: str, reference_text: str) -> Dict:
    """检查用户输入是否与参考文本意思一致（部分一致即可）"""
    from .app import chatgpt_streamed_async
    import asyncio
    import json
    
    prompt = f"""判断以下两个英文句子的意思是否一致。

参考句子：{reference_text}
用户输入：{user_input}

要求：
1. 如果意思一致或部分一致（即使表达不同），返回 "consistent"
2. 如果用户输入明显偏离主题或完全无关（瞎说），返回 "inconsistent"
3. 如果用户输入为空或几乎没有内容（不说），返回 "inconsistent"
4. 如果用户输入有明显语法错误但不影响理解，返回 "consistent_with_errors"

注意：只要意思相关，即使表达方式不同，也应该返回 "consistent"。

只返回JSON格式，不要其他说明：
{{"result": "consistent/inconsistent/consistent_with_errors", "reason": "简要说明原因"}}"""
    
    response = await chatgpt_streamed_async(
        prompt,
        "你是一个专业的英语教学助手，能够判断句子意思的一致性。",
        "neutral",
        []
    )
    
    # 尝试解析JSON
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error parsing validation result: {e}")
    
    # 默认返回一致（如果解析失败，给用户机会）
    return {"result": "consistent", "reason": "无法判断，默认通过"}

async def extract_hints(reference_text: str) -> Dict:
    """从参考文本中提取提示信息"""
    from .app import chatgpt_streamed_async
    import asyncio
    import json
    
    prompt = f"""从以下英文句子中提取学习提示：

句子：{reference_text}

要求提取：
1. 关键词组（key phrases）：2-3个重要词组或短语
2. 句型结构（sentence pattern）：句子的主要语法结构
3. 重点词汇（key words）：2-3个重点单词
4. 语法点（grammar points）：涉及的语法知识（简要说明）

返回JSON格式，不要其他说明：
{{
    "phrases": ["词组1", "词组2"],
    "pattern": "句型结构说明",
    "words": ["单词1", "单词2"],
    "grammar": "语法点说明"
}}"""
    
    response = await chatgpt_streamed_async(
        prompt,
        "你是一个专业的英语教学助手，能够提取句子中的学习要点。",
        "neutral",
        []
    )
    
    # 尝试解析JSON
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error parsing hints: {e}")
    
    # 默认返回空提示
    return {
        "phrases": [],
        "pattern": "",
        "words": [],
        "grammar": ""
    }


# 结束对话功能已移除（记忆系统已移除）

@app.get("/kokoro_voices")
async def get_kokoro_voices():
    try:
        # Get the base URL from environment or use default
        kokoro_base_url = os.getenv("KOKORO_BASE_URL", "http://localhost:8880/v1")
        
        # Get authentication credentials
        kokoro_username = os.getenv("KOKORO_USERNAME", "")
        kokoro_password = os.getenv("KOKORO_PASSWORD", "")
        
        # Prepare auth headers if credentials are provided
        headers = {}
        if kokoro_username and kokoro_password:
            import base64
            auth_str = f"{kokoro_username}:{kokoro_password}"
            auth_bytes = auth_str.encode('ascii')
            base64_auth = base64.b64encode(auth_bytes).decode('ascii')
            headers["Authorization"] = f"Basic {base64_auth}"
        
        try:
            # Use the correct API endpoint for voices
            voices_url = f"{kokoro_base_url}/audio/voices"
            
            # Make HTTP request directly with SSL verification disabled
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                try:
                    async with session.get(voices_url, headers=headers, timeout=3) as response:
                        if response.status == 200:
                            data = await response.json()
                            # Process the voices from the response
                            voices = []
                            
                            # Language/accent codes mapping
                            language_codes = {
                                'a': 'American English',
                                'b': 'British English',
                                'e': 'European Spanish',
                                'f': 'French',
                                'g': 'German',
                                'h': 'Hindi',
                                'i': 'Italian',
                                'j': 'Japanese',
                                'k': 'Korean',
                                'p': 'Polish',
                                'r': 'Russian',
                                's': 'Spanish',
                                'z': 'Chinese'
                            }
                            
                            # Get all voice IDs
                            voice_ids = data.get("voices", [])
                            
                            # Group voices by language/accent
                            english_voices = []  # American and British English
                            other_voices_by_language = {}  # Organize other voices by language code
                            unknown_voices = []
                            
                            for voice_id in voice_ids:
                                parts = voice_id.split('_')
                                if len(parts) >= 2:
                                    lang_code = parts[0]
                                    # First character is language code
                                    accent_code = lang_code[:1]
                                    
                                    # Prioritize English voices (American and British)
                                    if accent_code in ['a', 'b']:
                                        english_voices.append(voice_id)
                                    else:
                                        # Group other voices by language
                                        if accent_code not in other_voices_by_language:
                                            other_voices_by_language[accent_code] = []
                                        other_voices_by_language[accent_code].append(voice_id)
                                else:
                                    unknown_voices.append(voice_id)
                            
                            # Sort voices within each group
                            english_voices.sort()
                            for lang in other_voices_by_language:
                                other_voices_by_language[lang].sort()
                            unknown_voices.sort()
                            
                            # Create final sorted list: English first, then other languages alphabetically
                            sorted_voice_ids = english_voices
                            
                            # Process English voices
                            for voice_id in english_voices:
                                parts = voice_id.split('_')
                                if len(parts) >= 2:
                                    lang_code = parts[0]
                                    name = parts[1].capitalize()
                                    
                                    accent_code = lang_code[:1]
                                    gender_code = lang_code[1:2]
                                    
                                    gender = "Female" if gender_code == "f" else "Male"
                                    accent_label = f" - {language_codes.get(accent_code, 'Unknown')}"
                                    
                                    voices.append({
                                        "id": voice_id,
                                        "name": f"{name} ({gender}){accent_label}"
                                    })
                            
                            # Add other language groups with separators
                            for lang in sorted(other_voices_by_language.keys()):
                                # Add a language group header if we have voices for this language
                                if other_voices_by_language[lang]:
                                    language_name = language_codes.get(lang, "Unknown Language")
                                    
                                    # Add a separator for this language group
                                    voices.append({
                                        "id": f"separator_{lang}",
                                        "name": f"--- {language_name} Voices ---"
                                    })
                                    
                                    # Add the voices for this language
                                    for voice_id in other_voices_by_language[lang]:
                                        parts = voice_id.split('_')
                                        if len(parts) >= 2:
                                            name = parts[1].capitalize()
                                            gender_code = parts[0][1:2]
                                            gender = "Female" if gender_code == "f" else "Male"
                                            
                                            voices.append({
                                                "id": voice_id,
                                                "name": f"{name} ({gender})"
                                            })
                            
                            # Add unknown voices at the end if any
                            if unknown_voices:
                                voices.append({
                                    "id": "separator_unknown",
                                    "name": "--- Other Voices ---"
                                })
                                
                                for voice_id in unknown_voices:
                                    voices.append({
                                        "id": voice_id,
                                        "name": voice_id
                                    })
                            
                            return {"voices": voices}
                        else:
                            # Log the error and return empty voices
                            error_text = await response.text()
                            logger.error(f"Error fetching Kokoro voices: HTTP {response.status} - {error_text}")
                            return {"voices": [], "error": f"HTTP Error: {response.status}"}
                except aiohttp.ClientConnectorError as e:
                    # Handle connection errors specifically (server not available)
                    logger.info(f"Kokoro server not available at {kokoro_base_url} - This is normal if you don't have Kokoro running")
                    return {"voices": [], "error": "Kokoro server not available"}
                except asyncio.TimeoutError:
                    # Handle timeout errors
                    # logger.info(f"Timeout connecting to Kokoro server at {kokoro_base_url}")
                    return {"voices": [], "error": "Connection timeout"}
            
        except Exception as e:
            # Log the error and return empty voices with error message
            logger.error(f"Error fetching Kokoro voices: {str(e)}")
            return {"voices": [], "error": str(e)}
            
    except Exception as e:
        logger.error(f"Critical error in get_kokoro_voices: {str(e)}")
        return {"voices": [], "error": str(e)}

def signal_handler(sig, frame):
    print('\nShutting down gracefully... Press Ctrl+C again to force exit')
    
    try:
        # Stop any active enhanced conversation
        try:
            # For async shutdown in sync context, create a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # First stop any active conversations
            from .enhanced_logic import enhanced_conversation_active, stop_enhanced_conversation
            if enhanced_conversation_active:
                print("Stopping active enhanced conversation...")
                loop.run_until_complete(stop_enhanced_conversation())
                
            # Then close all WebSocket connections
            for client in list(clients):  # Create a copy of the clients set to avoid modification during iteration
                try:
                    if hasattr(client, 'close'):
                        # Use the same loop for consistency
                        loop.run_until_complete(client.close())
                except Exception as e:
                    print(f"Error closing client: {e}")
                    
            loop.close()
        except Exception as e:
            print(f"Error in graceful shutdown: {e}")
        
        print("Shutdown procedures completed. Exiting...")
        import os
        os._exit(0)  # Force exit as sys.exit() might not work if asyncio is running
        
    except Exception as e:
        print(f"Error during shutdown: {e}")
        import os
        os._exit(1)  # Error exit code

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("Starting server. Press Ctrl+C to exit.")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nServer stopped by keyboard interrupt.")
    finally:
        print("Shutdown complete.")