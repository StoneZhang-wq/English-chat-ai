import json
import os
import signal
import uvicorn
import asyncio
from datetime import datetime
from typing import Dict
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, JSONResponse
from starlette.background import BackgroundTask
from .shared import clients, set_current_character, conversation_history, add_client, remove_client, get_memory_system, set_current_account, get_current_account
from .app_logic import start_conversation, stop_conversation, set_env_variable, characters_folder, set_transcription_model, fetch_ollama_models, load_character_prompt, load_character_specific_history
from .enhanced_logic import start_enhanced_conversation, stop_enhanced_conversation
from .app import send_message_to_clients
import logging
from threading import Thread
import uuid
import aiohttp
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

# Mount static files and templates
app.mount("/app/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

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
    model_provider = os.getenv("MODEL_PROVIDER")
    character_name = os.getenv("CHARACTER_NAME", "english_tutor") 
    tts_provider = os.getenv("TTS_PROVIDER")
    openai_tts_voice = os.getenv("OPENAI_TTS_VOICE")
    openai_model = os.getenv("OPENAI_MODEL")
    ollama_model = os.getenv("OLLAMA_MODEL")
    voice_speed = os.getenv("VOICE_SPEED")
    elevenlabs_voice = os.getenv("ELEVENLABS_TTS_VOICE")
    kokoro_voice = os.getenv("KOKORO_TTS_VOICE")
    faster_whisper_local = os.getenv("FASTER_WHISPER_LOCAL", "true").lower() == "true"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "model_provider": model_provider,
        "character_name": character_name,
        "tts_provider": tts_provider,
        "openai_tts_voice": openai_tts_voice,
        "openai_model": openai_model,
        "ollama_model": ollama_model,
        "voice_speed": voice_speed,
        "elevenlabs_voice": elevenlabs_voice,
        "kokoro_voice": kokoro_voice,
        "faster_whisper_local": faster_whisper_local,
    })

@app.get("/voice_chat", response_class=HTMLResponse)
async def get_voice_chat(request: Request):
    """Instagram风格的语音消息界面"""
    character_name = os.getenv("CHARACTER_NAME", "english_tutor")
    return templates.TemplateResponse("voice_chat.html", {
        "request": request,
        "character_name": character_name,
    })

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
            return JSONResponse({
                "status": "error",
                "message": "初始化记忆系统失败"
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
            elif message["action"] == "set_provider":
                set_env_variable("MODEL_PROVIDER", message["provider"])
            elif message["action"] == "set_tts":
                set_env_variable("TTS_PROVIDER", message["tts"])
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
        from .shared import get_memory_system, get_current_character, get_learning_stage
        
        memory_system = get_memory_system()
        if not memory_system:
            return JSONResponse({
                "status": "error",
                "message": "记忆系统未初始化"
            }, status_code=500)
        
        current_character = get_current_character()
        learning_stage = get_learning_stage()
        
        # 从临时文件生成摘要
        entry = await memory_system.generate_diary_summary_from_temp(current_character)
        
        today_summary = ""
        if entry:
            memory_system.add_diary_entry(entry)
            today_summary = entry.get("summary", "")
            
            # 从会话中提取用户信息
            session_data = memory_system.load_session_temp()
            if session_data and session_data.get("messages"):
                conversation_text = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in session_data["messages"]
                ])
                extracted_info = await memory_system.extract_user_info(conversation_text)
                # extract_user_info 内部已经调用了 update_user_profile
        
        # 清空临时会话文件
        memory_system.clear_session_temp()
        
        # 总是允许生成英文对话（即使没有今天的摘要，也可以基于历史记忆生成）
        response_data = {
            "status": "success",
            "message": "对话已结束，记忆已保存",
            "summary": today_summary,
            "timestamp": entry.get("timestamp", "") if entry else "",
            "should_generate_english": True  # 总是允许生成英文对话
        }
        
        if today_summary:
            response_data["message"] = "对话已结束，记忆已保存。可以生成英文学习对话了"
        else:
            response_data["message"] = "可以生成英文学习对话了（将基于历史记忆生成）"
        
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
    """生成英文教学对话"""
    try:
        from .shared import get_memory_system, get_current_character, get_learning_stage, set_learning_stage
        
        data = await request.json()
        dialogue_length = data.get("dialogue_length", "auto")  # short/medium/long/custom/auto
        difficulty_level = data.get("difficulty_level", None)  # 新增：难度水平，如果为None则使用用户当前水平
        custom_sentence_count = data.get("custom_sentence_count", None)
        
        memory_system = get_memory_system()
        if not memory_system:
            return JSONResponse({
                "status": "error",
                "message": "记忆系统未初始化"
            }, status_code=500)
        
        # 获取今天的中文对话摘要（从日记条目中获取）
        current_character = get_current_character()
        today_summary = ""
        
        diary_entries = memory_system.diary_data.get("entries", [])
        if diary_entries:
            today = datetime.now().strftime("%Y-%m-%d")
            today_entries = [e for e in diary_entries if e.get("date") == today]
            if today_entries:
                # 获取今天最新的摘要
                today_summary = today_entries[-1].get("summary", "")
        
        # 生成英文对话，传入难度参数
        english_dialogue_result = await memory_system.generate_english_dialogue(
            today_summary, 
            dialogue_length,
            difficulty_level,
            custom_sentence_count
        )
        
        if english_dialogue_result:
            # 切换到英文学习阶段
            set_learning_stage("english_learning")
            
            # 处理返回格式：可能是字典（新格式）或字符串（旧格式兼容）
            if isinstance(english_dialogue_result, dict):
                return JSONResponse({
                    "status": "success",
                    "message": "英文对话已生成",
                    "dialogue": english_dialogue_result.get("dialogue_text", ""),
                    "dialogue_lines": english_dialogue_result.get("dialogue_lines", []),
                    "dialogue_id": english_dialogue_result.get("dialogue_id", "")
                })
            else:
                # 兼容旧格式（纯文本）
                return JSONResponse({
                    "status": "success",
                    "message": "英文对话已生成",
                    "dialogue": english_dialogue_result
                })
        else:
            logger.error("generate_english_dialogue returned None or empty result")
            return JSONResponse({
                "status": "error",
                "message": "生成英文对话失败：AI生成对话时出错，请检查控制台日志获取详细信息"
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"Error generating english dialogue: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"生成英文对话时出错: {str(e)}"
        }, status_code=500)

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
    """开始练习阶段，解析对话卡片并初始化状态"""
    try:
        from .shared import get_memory_system
        from .app import chatgpt_streamed
        import asyncio
        import uuid
        
        data = await request.json()
        dialogue = data.get("dialogue", "").strip()
        dialogue_lines_from_card = data.get("dialogue_lines", [])  # 从英语卡片获取的对话行（包含音频URL）
        dialogue_id_from_card = data.get("dialogue_id", "")  # 从英语卡片获取的对话ID
        
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
        
        # 确保对话以A开始
        if dialogue_lines[0]["speaker"] != "A":
            return JSONResponse({
                "status": "error",
                "message": "对话必须以A（AI）开始"
            }, status_code=400)
        
        # 使用卡片提供的对话ID，或生成新的
        dialogue_id = dialogue_id_from_card if dialogue_id_from_card else f"practice_{int(datetime.now().timestamp() * 1000)}"
        
        # 生成会话ID用于跟踪练习会话
        session_id = str(uuid.uuid4())
        
        # 从对话内容中智能提取主题（使用AI分析）
        all_dialogue_text = " ".join([line.get("text", "") for line in dialogue_lines])
        dialogue_topic = "日常对话"  # 默认主题
        
        try:
            topic_prompt = f"""分析以下英文对话，提取出主要讨论的主题（1-2个中文关键词，如：电影、篮球、学习、工作等）：

{all_dialogue_text}

只返回主题关键词，用中文，用逗号分隔，例如：电影,篮球 或 学习,工作。不要其他说明。"""
            
            loop = asyncio.get_event_loop()
            topic_response = await loop.run_in_executor(
                None,
                lambda: chatgpt_streamed(
                    topic_prompt,
                    "你是一个专业的英语教学助手，能够准确分析对话主题。只返回主题关键词，不要其他说明。",
                    "neutral",
                    []
                )
            )
            # 提取主题关键词
            if topic_response:
                topics = [t.strip() for t in topic_response.strip().split(",") if t.strip()]
                dialogue_topic = ", ".join(topics[:2]) if topics else "日常对话"
        except Exception as e:
            logger.error(f"Error extracting dialogue topic: {e}")
            dialogue_topic = "日常对话"  # 失败时使用默认值
        
        # 初始化练习会话记录
        practice_sessions[session_id] = {
            "dialogue_id": dialogue_id,
            "dialogue_lines": dialogue_lines,
            "user_inputs": [],  # 存储对话上下文（ai_said, user_said）
            "dialogue_topic": dialogue_topic,
            "start_time": datetime.now().isoformat()
        }
        
        # 获取第一句A的台词和对应的B的提示
        first_a_text = dialogue_lines[0]["text"]
        first_a_audio_url = dialogue_lines[0].get("audio_url")  # 获取音频URL
        first_b_text = None
        if len(dialogue_lines) > 1 and dialogue_lines[1]["speaker"] == "B":
            first_b_text = dialogue_lines[1]["text"]
        
        # 如果有B的台词，提取提示
        hints = None
        if first_b_text:
            try:
                hints = await extract_hints(first_b_text)
            except Exception as e:
                logger.error(f"Error extracting hints: {e}")
                # 如果提取提示失败，使用空提示，不影响练习开始
                hints = {
                    "phrases": [],
                    "pattern": "",
                    "words": [],
                    "grammar": ""
                }
        
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
        from .app import chatgpt_streamed
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
                                # 如果A后面还有B，提取B的提示
                                if j + 1 < len(dialogue_lines) and dialogue_lines[j + 1]["speaker"] == "B":
                                    next_b_hints = await extract_hints(dialogue_lines[j + 1]["text"])
                                    is_completed = False  # 还有下一轮，未完成
                                else:
                                    # A后面没有B了，说明这是最后一个A，练习应该完成
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
        
        # 获取会话数据
        session_data = practice_sessions[session_id].copy()
        session_data["end_time"] = datetime.now().isoformat()
        
        # 从对话内容和用户实际练习内容中智能提取主题
        dialogue_topic = session_data.get("dialogue_topic", "日常对话")
        
        # 如果之前没有提取主题，或者需要重新确认，从实际对话内容中提取
        all_text = " ".join([line.get("text", "") for line in session_data.get("dialogue_lines", [])])
        user_practice_text = " ".join([
            item.get("ai_said", "") + " " + item.get("user_said", "") 
            for item in session_data.get("user_inputs", [])
        ])
        
        # 结合对话内容和用户实际练习内容来提取主题
        combined_text = f"{all_text} {user_practice_text}".strip()
        
        if combined_text:
            try:
                from .app import chatgpt_streamed
                topic_prompt = f"""分析以下英文对话和用户练习内容，提取出主要讨论的主题（1-2个中文关键词）：

对话内容：
{all_text}

用户实际练习内容：
{user_practice_text}

只返回主题关键词，用中文，用逗号分隔，例如：电影,篮球。不要其他说明。"""
                
                loop = asyncio.get_event_loop()
                topic_response = await loop.run_in_executor(
                    None,
                    lambda: chatgpt_streamed(
                        topic_prompt,
                        "你是一个专业的英语教学助手，能够准确分析对话主题。只返回主题关键词，不要其他说明。",
                        "neutral",
                        []
                    )
                )
                if topic_response:
                    topics = [t.strip() for t in topic_response.strip().split(",") if t.strip()]
                    dialogue_topic = ", ".join(topics[:2]) if topics else dialogue_topic
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error extracting dialogue topic in end_practice: {e}")
                # 如果AI提取失败，保持原有主题
        
        session_data["dialogue_topic"] = dialogue_topic
        
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

@app.post("/api/practice/hints")
async def get_practice_hints(request: Request):
    """获取提示信息（按需）"""
    try:
        from .shared import get_memory_system
        
        data = await request.json()
        reference_text = data.get("reference_text", "").strip()
        
        if not reference_text:
            return JSONResponse({
                "status": "error",
                "message": "参考文本不能为空"
            }, status_code=400)
        
        hints = await extract_hints(reference_text)
        
        return JSONResponse({
            "status": "success",
            "hints": hints
        })
        
    except Exception as e:
        logger.error(f"Error getting hints: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"获取提示时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/practice/generate-review")
async def generate_review_notes(request: Request):
    """生成复习笔记"""
    try:
        from .shared import get_memory_system
        from .app import chatgpt_streamed
        import asyncio
        import json
        
        data = await request.json()
        user_inputs = data.get("user_inputs", [])  # [{turn, ai_said, user_said}, ...]
        dialogue_topic = data.get("dialogue_topic", "日常对话")
        
        if not user_inputs:
            return JSONResponse({
                "status": "error",
                "message": "用户输入数据不能为空"
            }, status_code=400)
        
        # 构建对话上下文的文本（AI说的和用户说的）
        user_inputs_text = "\n".join([
            f"轮次 {item['turn']}:\n  AI说: {item.get('ai_said', '')}\n  用户说: {item.get('user_said', '')}"
            for item in user_inputs
        ])
        
        # 构建生成复习笔记的prompt
        prompt = f"""基于以下练习会话数据，生成个性化的复习笔记。

对话主题：{dialogue_topic}

用户输入和参考台词：
{user_inputs_text}

请生成包含以下内容的复习笔记（JSON格式）：
{{
  "vocabulary": {{
    "key_words": ["重点词汇1", "重点词汇2", ...],
    "new_words": ["新词汇1", "新词汇2", ...],
    "difficult_words": ["易错词汇1", "易错词汇2", ...]
  }},
  "grammar": [
    {{
      "point": "语法点名称",
      "user_usage": "用户使用的语法（如果有错误）",
      "correct_usage": "正确用法",
      "explanation": "解释说明"
    }},
    ...
  ],
  "corrections": [
    {{
      "user_said": "用户说的内容",
      "correct": "正确表达",
      "explanation": "错误原因和纠正说明"
    }},
    ...
  ],
  "suggestions": [
    "针对性的学习建议1",
    "针对性的学习建议2",
    ...
  ]
}}

要求：
1. 词汇部分要包含用户在练习中使用的重要词汇、新出现的词汇、容易出错的词汇
2. 语法点要分析用户使用的语法，指出错误（如果有）并提供正确用法
3. 错误纠正要对比用户说的内容和参考台词，指出差异和正确表达
4. 改进建议要针对用户的具体表现给出学习建议
5. 只返回JSON格式，不要其他文字说明
"""
        
        # 调用AI生成
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chatgpt_streamed(
                prompt,
                "你是一个专业的英语教学助手，能够分析学生的练习表现并生成个性化的复习笔记。",
                "neutral",
                []
            )
        )
        
        if not response or not response.strip():
            return JSONResponse({
                "status": "error",
                "message": "AI生成失败，返回空响应"
            }, status_code=500)
        
        # 尝试解析JSON响应
        try:
            # 提取JSON部分
            response_text = response.strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                review_notes = json.loads(json_str)
            else:
                # 如果没有找到JSON，返回错误
                logger.error(f"Failed to parse review notes JSON: {response_text[:200]}")
                return JSONResponse({
                    "status": "error",
                    "message": "无法解析AI返回的复习笔记格式"
                }, status_code=500)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response: {response_text[:200]}")
            return JSONResponse({
                "status": "error",
                "message": f"解析复习笔记JSON失败: {str(e)}"
            }, status_code=500)
        
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

@app.post("/api/practice/generate-expansion")
async def generate_expansion_materials(request: Request):
    """生成场景拓展资料"""
    try:
        from .shared import get_memory_system
        from .app import chatgpt_streamed
        import asyncio
        import json
        
        data = await request.json()
        dialogue_topic = data.get("dialogue_topic", "日常对话")
        user_inputs = data.get("user_inputs", [])  # 获取用户实际练习内容
        user_level = data.get("user_level", "beginner")  # 可选：用户水平
        
        # 基于用户实际练习内容提取主题
        actual_practice_topics = []
        if user_inputs:
            # 从用户输入中提取实际练习的主题
            user_text = " ".join([
                item.get("ai_said", "") + " " + item.get("user_said", "") 
                for item in user_inputs
            ])
            
            if user_text.strip():
                try:
                    topic_prompt = f"""分析以下英语练习对话，提取出主要讨论的主题（1-3个中文关键词）：

{user_text}

只返回主题关键词，用中文，用逗号分隔，例如：电影,篮球,娱乐。不要其他说明。"""
                    
                    loop = asyncio.get_event_loop()
                    topic_response = await loop.run_in_executor(
                        None,
                        lambda: chatgpt_streamed(
                            topic_prompt,
                            "你是一个专业的英语教学助手，能够分析对话主题。只返回主题关键词，不要其他说明。",
                            "neutral",
                            []
                        )
                    )
                    if topic_response:
                        actual_practice_topics = [t.strip() for t in topic_response.strip().split(",") if t.strip()]
                except Exception as e:
                    logger.error(f"Error extracting practice topics: {e}")
        
        # 使用实际练习主题，如果没有则使用dialogue_topic
        actual_topic = ", ".join(actual_practice_topics) if actual_practice_topics else dialogue_topic
        
        # 构建生成场景拓展资料的prompt
        prompt = f"""基于以下实际练习内容，生成场景拓展资料。

实际练习主题：{actual_topic}
原始对话主题：{dialogue_topic}

用户实际练习内容：
{chr(10).join([f"- AI: {item.get('ai_said', '')}{chr(10)}  用户: {item.get('user_said', '')}" for item in user_inputs[:5]]) if user_inputs else "无"}

用户水平：{user_level}

请生成场景拓展资料（JSON格式）：
{{
  "dialogues": [
    {{
      "scene": "场景名称",
      "dialogue": [
        {{"speaker": "A", "text": "..."}},
        {{"speaker": "B", "text": "..."}},
        ...
      ]
    }},
    ...
  ],
  "expressions": [
    {{
      "phrase": "常用短语或句型",
      "meaning": "中文意思",
      "example": "使用示例"
    }},
    ...
  ]
}}

要求：
1. 场景拓展必须与用户实际练习的主题相关（{actual_topic}），而不是原始对话主题
2. 对话示例：生成3-5个与用户实际练习主题相关的不同场景对话（每个对话包含A和B的对话，约4-6句）
3. 常用表达：提供该场景下的常用短语、句型，每个表达要有中文意思和使用示例
4. 对话要自然流畅，符合真实场景
5. 表达要实用，能帮助用户在实际场景中应用
6. 只返回JSON格式，不要其他文字说明
"""
        
        # 调用AI生成
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chatgpt_streamed(
                prompt,
                "你是一个专业的英语教学助手，能够生成场景相关的对话示例和常用表达。",
                "neutral",
                []
            )
        )
        
        if not response or not response.strip():
            return JSONResponse({
                "status": "error",
                "message": "AI生成失败，返回空响应"
            }, status_code=500)
        
        # 尝试解析JSON响应
        try:
            # 提取JSON部分
            response_text = response.strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                expansion_materials = json.loads(json_str)
            else:
                # 如果没有找到JSON，返回错误
                logger.error(f"Failed to parse expansion materials JSON: {response_text[:200]}")
                return JSONResponse({
                    "status": "error",
                    "message": "无法解析AI返回的场景拓展资料格式"
                }, status_code=500)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response: {response_text[:200]}")
            return JSONResponse({
                "status": "error",
                "message": f"解析场景拓展资料JSON失败: {str(e)}"
            }, status_code=500)
        
        return JSONResponse({
            "status": "success",
            "expansion_materials": expansion_materials
        })
        
    except Exception as e:
        logger.error(f"Error generating expansion materials: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "status": "error",
            "message": f"生成场景拓展资料时出错: {str(e)}"
        }, status_code=500)

@app.post("/api/practice/save-memory")
async def save_practice_memory(request: Request):
    """保存练习记忆到文件"""
    try:
        from .shared import get_memory_system
        
        data = await request.json()
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
    from .app import chatgpt_streamed
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
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: chatgpt_streamed(
            prompt,
            "你是一个专业的英语教学助手，能够判断句子意思的一致性。",
            "neutral",
            []
        )
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
    from .app import chatgpt_streamed
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
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: chatgpt_streamed(
            prompt,
            "你是一个专业的英语教学助手，能够提取句子中的学习要点。",
            "neutral",
            []
        )
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