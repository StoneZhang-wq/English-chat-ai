"""
场景-NPC 数据库：仅从 dialogues.json 加载，管理解锁状态
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# 模块加载时解析并缓存项目根目录，避免重复计算
_PROJECT_DIR: Optional[Path] = None
_DIALOGUES_CACHE: Optional[List[Dict]] = None
_SCENE_INDEX: Optional[Dict[str, Any]] = None


def _project_dir() -> Path:
    """项目根目录。优先用环境变量 VOICE_CHAT_PROJECT_ROOT，否则按 __file__ 推导"""
    global _PROJECT_DIR
    if _PROJECT_DIR is not None:
        return _PROJECT_DIR
    env_root = os.environ.get("VOICE_CHAT_PROJECT_ROOT", "").strip()
    if env_root:
        p = Path(env_root)
        if p.is_dir():
            _PROJECT_DIR = p.resolve()
            return _PROJECT_DIR
    # 按 __file__ 推导：scene_npc_db 在 app/ 下，parent.parent = 项目根
    _PROJECT_DIR = Path(__file__).resolve().parent.parent
    return _PROJECT_DIR


def _data_dir() -> Path:
    return _project_dir() / "data"


def _memory_dir() -> Path:
    return _project_dir() / "memory" / "accounts"


def _dialogues_path() -> Path:
    """dialogues.json 的路径"""
    return _data_dir() / "dialogues.json"


def _index_path() -> Path:
    """scene_npc_index.json 的路径（由 scripts/build_scene_npc_index.py 生成）"""
    return _data_dir() / "scene_npc_index.json"


def _scenes_images_dir() -> Path:
    """场景本地图片目录：与 data/ 同项目根，保证与 StaticFiles 一致。"""
    return _project_dir() / "app" / "static" / "images" / "scenes"


_SCENE_IMAGE_URL_CACHE: Dict[str, str] = {}


def clear_scene_image_url_cache() -> None:
    """清空场景图片 URL 缓存，下次请求会重新按磁盘文件(.png 优先于 .svg)解析。"""
    global _SCENE_IMAGE_URL_CACHE
    _SCENE_IMAGE_URL_CACHE.clear()


_IMAGE_EXTS = (".jpg", ".png", ".jpeg", ".webp", ".svg")


def _scene_image_url(small_scene_id: str) -> str:
    """根据 small_scene_id 返回本地图 URL，无则用 default.svg。带 ?t=mtime 防浏览器强缓存。"""
    if not small_scene_id:
        return "/app/static/images/scenes/default.svg"
    key = f"small:{small_scene_id}"
    if key in _SCENE_IMAGE_URL_CACHE:
        return _SCENE_IMAGE_URL_CACHE[key]
    base = _scenes_images_dir()
    for ext in _IMAGE_EXTS:
        p = base / f"{small_scene_id}{ext}"
        if p.is_file():
            try:
                mtime = int(p.stat().st_mtime)
                url = f"/app/static/images/scenes/{small_scene_id}{ext}?t={mtime}"
            except OSError:
                url = f"/app/static/images/scenes/{small_scene_id}{ext}"
            _SCENE_IMAGE_URL_CACHE[key] = url
            return url
    url = "/app/static/images/scenes/default.svg"
    _SCENE_IMAGE_URL_CACHE[key] = url
    return url


def _big_scene_image_url(big_scene_id: str) -> str:
    """大场景图：文件名 big_{id}.ext，缺省 default_big.svg。"""
    if not big_scene_id:
        return "/app/static/images/scenes/default_big.svg"
    key = f"big:{big_scene_id}"
    if key in _SCENE_IMAGE_URL_CACHE:
        return _SCENE_IMAGE_URL_CACHE[key]
    base = _scenes_images_dir()
    name = f"big_{big_scene_id}"
    for ext in _IMAGE_EXTS:
        p = base / f"{name}{ext}"
        if p.is_file():
            try:
                mtime = int(p.stat().st_mtime)
                url = f"/app/static/images/scenes/{name}{ext}?t={mtime}"
            except OSError:
                url = f"/app/static/images/scenes/{name}{ext}"
            _SCENE_IMAGE_URL_CACHE[key] = url
            return url
    url = "/app/static/images/scenes/default_big.svg"
    _SCENE_IMAGE_URL_CACHE[key] = url
    return url


def _npc_image_url(character_id: str) -> str:
    """NPC 图：文件名 npc_{character_id}.ext（character_id 如 home_family），缺省统一使用简单人像 npc_avatar.svg。"""
    if not character_id:
        return "/app/static/images/scenes/npc_avatar.svg"
    key = f"npc:{character_id}"
    if key in _SCENE_IMAGE_URL_CACHE:
        return _SCENE_IMAGE_URL_CACHE[key]
    base = _scenes_images_dir()
    name = f"npc_{character_id}"
    for ext in _IMAGE_EXTS:
        p = base / f"{name}{ext}"
        if p.is_file():
            try:
                mtime = int(p.stat().st_mtime)
                url = f"/app/static/images/scenes/{name}{ext}?t={mtime}"
            except OSError:
                url = f"/app/static/images/scenes/{name}{ext}"
            _SCENE_IMAGE_URL_CACHE[key] = url
            return url
    url = "/app/static/images/scenes/npc_avatar.svg"
    _SCENE_IMAGE_URL_CACHE[key] = url
    return url


def _load_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = []
    path_str = str(path.resolve())
    try:
        if not path.exists():
            logger.warning("JSON 文件不存在: %s", path_str)
            return default
        with open(path_str, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 仅当期望 list（如 dialogues.json）时校验类型；dict（如 npc_learn_progress.json）直接返回
        if isinstance(default, list) and not isinstance(data, list):
            logger.warning("JSON 格式错误，应为数组: %s", path_str)
            return default
        return data
    except json.JSONDecodeError as e:
        logger.warning("dialogues.json 解析失败 %s: %s", path_str, e)
    except OSError as e:
        logger.warning("读取 dialogues.json 失败 %s: %s", path_str, e)
    except Exception as e:
        logger.warning("加载 dialogues.json 异常 %s: %s", path_str, e)
    return default

def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 少数 small_scene_id 与 immersive_scene_id 不同（源自原 scene_npc_config）
_IMMERSIVE_SCENE_OVERRIDE: Dict[str, str] = {"hospital": "clinic"}

def _to_immersive_scene_id(small_scene_id: str) -> str:
    return _IMMERSIVE_SCENE_OVERRIDE.get(small_scene_id, small_scene_id)

def get_dialogues() -> List[Dict]:
    """返回 dialogues.json 全部记录。首次加载后缓存，避免路径/读取波动"""
    global _DIALOGUES_CACHE
    if _DIALOGUES_CACHE is not None:
        return _DIALOGUES_CACHE
    path = _dialogues_path()
    data = _load_json(path, [])
    _DIALOGUES_CACHE = data
    if data:
        logger.info("已加载 dialogues.json: %s，共 %d 条", path, len(data))
    else:
        logger.warning("dialogues.json 加载为空，路径: %s", path)
    return data


def reload_dialogues() -> None:
    """强制重新加载 dialogues.json 与场景索引（用于配置变更后）"""
    global _DIALOGUES_CACHE, _SCENE_INDEX
    _DIALOGUES_CACHE = None
    _SCENE_INDEX = None
    clear_scene_image_url_cache()


def _load_scene_index() -> Optional[Dict[str, Any]]:
    """加载 scene_npc_index.json，首次加载后缓存。不存在时返回 None，后端回退到现场推导。"""
    global _SCENE_INDEX
    if _SCENE_INDEX is not None:
        return _SCENE_INDEX
    path = _index_path()
    if not path.is_file():
        logger.debug("场景索引未找到 %s，将现场推导", path)
        return None
    data = _load_json(path, {})
    if not isinstance(data, dict) or "big_scenes" not in data:
        logger.warning("scene_npc_index.json 格式异常，将现场推导")
        return None
    _SCENE_INDEX = data
    logger.info("已加载场景索引: %s", path)
    return _SCENE_INDEX

# --- 解锁状态 ---

def _safe_account(account_name: Optional[str]) -> str:
    """确保账户名有效，空值用 default"""
    name = (account_name or "").strip()
    return name if name else "default"

def _unlock_path(account_name: str) -> Path:
    return _memory_dir() / _safe_account(account_name) / "small_scene_unlock.json"

def _npc_progress_path(account_name: str) -> Path:
    """记录每个小场景下已完成的 NPC（学完 learn 对话）"""
    return _memory_dir() / _safe_account(account_name) / "npc_learn_progress.json"

def _get_scenes_with_immersive_dialogues() -> set:
    """返回有 immersive 对话的 small_scene_id 集合"""
    seen = set()
    for d in get_dialogues():
        if d.get("usage") == "immersive":
            sid = d.get("small_scene")
            if sid:
                seen.add(sid)
    return seen

def _ensure_default_unlocks(account_name: str) -> None:
    """确保所有有沉浸式对话的场景默认解锁"""
    path = _unlock_path(account_name)
    data = _load_json(path, {})
    has_immersive = _get_scenes_with_immersive_dialogues()
    changed = False
    for sid in has_immersive:
        if sid and data.get(sid) is not True:
            data[sid] = True
            changed = True
    if changed:
        _save_json(path, data)

def get_unlocked_scenes(account_name: str) -> List[str]:
    """返回已解锁的 small_scene_id 列表。Supabase 时仅从 npc_learn_progress 推导，不读写本地 small_scene_unlock.json。"""
    backend = _npc_progress_backend(account_name)
    if backend is not None:
        has_immersive = _get_scenes_with_immersive_dialogues()
        progress = get_npc_progress(account_name)
        return [sid for sid in has_immersive if progress.get(sid)]
    acc = _safe_account(account_name)
    _ensure_default_unlocks(acc)
    data = _load_json(_unlock_path(acc), {})
    return [k for k, v in data.items() if v]

def _npc_progress_backend(account_name: str):
    """MEMORY_BACKEND=supabase 时用适配器，否则用本地文件。"""
    if os.getenv("MEMORY_BACKEND", "").strip().lower() == "supabase":
        from .adapters import get_memory_adapter
        return get_memory_adapter(account_name=account_name, project_dir=_project_dir())
    return None

def get_npc_progress(account_name: str) -> Dict[str, List[str]]:
    """返回 {small_scene_id: [npc_id, ...]} 已完成 learn 的 NPC"""
    backend = _npc_progress_backend(account_name)
    if backend is not None:
        return backend.load_npc_learn_progress()
    return _load_json(_npc_progress_path(account_name), {})

def mark_npc_learned(account_name: str, small_scene_id: str, npc_id: str) -> None:
    """标记某 NPC 的 learn 已完成"""
    backend = _npc_progress_backend(account_name)
    if backend is not None:
        data = backend.load_npc_learn_progress()
        if small_scene_id not in data:
            data[small_scene_id] = []
        if npc_id not in data[small_scene_id]:
            data[small_scene_id].append(npc_id)
        backend.save_npc_learn_progress(data)
        return
    data = get_npc_progress(account_name)
    if small_scene_id not in data:
        data[small_scene_id] = []
    if npc_id not in data[small_scene_id]:
        data[small_scene_id].append(npc_id)
    _save_json(_npc_progress_path(account_name), data)

def _get_npc_ids_with_learn_in_scene(small_scene_id: str) -> List[str]:
    """从 dialogues 中获取该小场景下所有有 learn 对话的 NPC id"""
    seen = set()
    for d in get_dialogues():
        if d.get("small_scene") == small_scene_id and d.get("usage") == "learn":
            nid = d.get("npc")
            if nid:
                seen.add(nid)
    return list(seen)

def check_and_unlock_scene(account_name: str, small_scene_id: str) -> bool:
    """若该小场景下所有 NPC 都已学完，则解锁；返回是否新解锁。Supabase 时不读写本地文件，仅按进度推导，返回 False（不区分是否「新」解锁）。"""
    npcs_in_scene = _get_npc_ids_with_learn_in_scene(small_scene_id)
    if not npcs_in_scene:
        return False
    progress = get_npc_progress(account_name)
    learned = set(progress.get(small_scene_id, []))
    if learned >= set(npcs_in_scene):
        if _npc_progress_backend(account_name) is not None:
            return False  # Supabase：不落盘解锁状态，无法得知是否「新解锁」
        unlock_data = _load_json(_unlock_path(account_name), {})
        was_unlocked = unlock_data.get(small_scene_id, False)
        unlock_data[small_scene_id] = True
        _save_json(_unlock_path(account_name), unlock_data)
        return not was_unlocked
    return False


def scene_can_enter(account_name: str, small_scene_id: str, progress: Optional[Dict[str, List[str]]] = None) -> bool:
    """该场景下是否至少有一个 NPC 已学完 learn 对话（满足则可进入沉浸场景）。传入 progress 可避免同请求内重复读文件。"""
    if progress is None:
        progress = get_npc_progress(account_name)
    learned = set(progress.get(small_scene_id, []))
    npcs_in_scene = _get_npc_ids_with_learn_in_scene(small_scene_id)
    return bool(learned & set(npcs_in_scene))

# --- 对话查询 ---

def get_dialogue(small_scene_id: str, npc_id: str, usage: str) -> Optional[Dict]:
    """按 small_scene, npc, usage 获取一条对话"""
    for d in get_dialogues():
        if d.get("small_scene") == small_scene_id and d.get("npc") == npc_id and d.get("usage") == usage:
            return d
    return None

def get_learn_dialogue(small_scene_id: str, npc_id: str) -> Optional[Dict]:
    return get_dialogue(small_scene_id, npc_id, "learn")

def get_review_dialogue(small_scene_id: str, npc_id: str) -> Optional[Dict]:
    return get_dialogue(small_scene_id, npc_id, "review")

def get_immersive_dialogue(small_scene_id: str, npc_id: str) -> Optional[Dict]:
    return get_dialogue(small_scene_id, npc_id, "immersive")


def build_card_title(dialogue: Dict) -> str:
    """根据对话记录生成卡片标题：在{小场景名}跟{NPC名}沟通。对 small_scene_name 做简单清洗。"""
    if not dialogue:
        return "英文学习对话"
    name_scene = (dialogue.get("small_scene_name") or "").strip()
    name_npc = (dialogue.get("npc_name") or "").strip()
    if not name_npc:
        return "英文学习对话"
    # 清洗：去掉 " / " 等，便于显示为「小区楼下」
    if name_scene:
        name_scene = name_scene.replace(" / ", "").replace("/", " ").strip()
    if not name_scene:
        name_scene = "该场景"
    return f"在{name_scene}跟{name_npc}沟通"


def get_big_scene_for_small_scene(small_scene_id: str) -> Optional[str]:
    """根据 small_scene_id 反查所属 big_scene_id（从 dialogues 取第一条匹配）"""
    for d in get_dialogues():
        if d.get("small_scene") == small_scene_id:
            return d.get("big_scene")
    return None


def infer_theme_scene_from_conversation(text: str) -> tuple:
    """从对话摘要/文本推断一个推荐的主题+场景 (big_scene_id, small_scene_id)。无法推断时返回 (None, None)。
    规则：内置关键词匹配，不调用 LLM。
    重要：每次更新 data/dialogues.json 或大/小场景、NPC 结构时，须同步更新本函数内的关键词与场景映射，以保持推荐与数据库一致。"""
    if not text or not text.strip():
        return (None, None)
    t = text.strip().lower()
    # 日常生活
    if any(k in t for k in ["家", "居家", "家人", "室友", "晚饭", "早餐"]):
        return ("daily", "home")
    if any(k in t for k in ["小区", "楼下", "快递", "外卖", "邻居", "保安"]):
        return ("daily", "community")
    if any(k in t for k in ["公园", "户外", "晨练", "路人"]):
        return ("daily", "park")
    if any(k in t for k in ["医院", "诊所", "医生", "护士", "挂号"]):
        return ("daily", "hospital")
    if any(k in t for k in ["银行", "柜员", "取钱", "办卡"]):
        return ("daily", "bank")
    # 餐饮
    if any(k in t for k in ["咖啡", "咖啡馆", "奶茶"]):
        return ("food", "cafe")
    if any(k in t for k in ["餐厅", "饭店", "点菜", "迎宾", "收银"]):
        return ("food", "restaurant")
    if any(k in t for k in ["快餐", "点餐"]):
        return ("food", "fast_food")
    if any(k in t for k in ["小吃", "奶茶店"]):
        return ("food", "snack_shop")
    # 出行交通
    if any(k in t for k in ["机场", "地勤", "安检", "空姐", "登机"]):
        return ("transport", "airport")
    if any(k in t for k in ["火车", "高铁", "售票", "检票", "火车站"]):
        return ("transport", "train_station")
    if any(k in t for k in ["地铁", "公交", "巴士", "司机", "售票员"]):
        return ("transport", "bus_metro")
    if any(k in t for k in ["出租车", "网约车", "打车", "的士"]):
        return ("transport", "taxi")
    if any(k in t for k in ["酒店", "宾馆", "入住", "退房", "客房", "前台"]):
        return ("transport", "hotel")
    # 购物消费
    if any(k in t for k in ["超市", "便利店", "收银", "导购"]):
        return ("shopping", "supermarket")
    if any(k in t for k in ["商场", "服装", "逛街", "试穿"]):
        return ("shopping", "mall")
    if any(k in t for k in ["理发", "剪发", "理发店"]):
        return ("shopping", "barber")
    if any(k in t for k in ["电影", "电影院", "售票", "检票"]):
        return ("shopping", "cinema")
    # 工作职场
    if any(k in t for k in ["办公室", "领导", "同事", "下属", "加班"]):
        return ("work", "office")
    if any(k in t for k in ["面试", "面试官", "求职"]):
        return ("work", "interview")
    if any(k in t for k in ["会议", "接待", "客户", "合作伙伴", "合同"]):
        return ("work", "meeting")
    if any(k in t for k in ["电话", "客服", "接线", "投诉"]):
        return ("work", "phone")
    # 社交人情
    if any(k in t for k in ["聚会", "朋友", "同学", "生日"]):
        return ("social", "party")
    if any(k in t for k in ["打招呼", "闲聊", "陌生人", "天气"]):
        return ("social", "chat")
    if any(k in t for k in ["兴趣", "爱好", "玩伴", "同好", "摄影", "运动"]):
        return ("social", "hobby")
    if any(k in t for k in ["赞美", "安慰", "道歉", "谢谢", "对不起"]):
        return ("social", "praise")
    return (None, None)


def get_recommended_anchor_from_history(account_name: str) -> tuple:
    """从用户练习记录中选一个 (big_scene_id, small_scene_id) 作为推荐锚点。无记录时返回 (None, None)。"""
    progress = get_npc_progress(account_name)
    if not progress:
        return (None, None)
    import random
    small_scene_ids = [sid for sid in progress if progress.get(sid)]
    if not small_scene_ids:
        return (None, None)
    sid = random.choice(small_scene_ids)
    bid = get_big_scene_for_small_scene(sid)
    return (bid, sid) if bid else (None, None)


def get_learning_recommendations(
    account_name: str,
    conversation_summary: Optional[str] = None,
    count: int = 4,
) -> List[Dict]:
    """
    获取学习推荐列表：优先从对话推断 1 个主题+场景，否则从练习记忆选 1 个。
    锚点场景会推荐该场景下全部 NPC；其余场景每场景随机 1 个。每项含 learned 标识。
    每项包含 big_scene_id, small_scene_id, npc_id, title, learned。
    """
    import random
    acc = _safe_account(account_name)
    progress = get_npc_progress(acc)
    big_scenes = _derive_big_scenes()
    scene_pairs: List[tuple] = []
    for b in big_scenes:
        bid = b.get("id")
        if not bid:
            continue
        for s in _derive_small_scenes_by_big(bid):
            sid = s.get("id")
            if sid:
                scene_pairs.append((bid, sid))
    if not scene_pairs:
        return []

    # 1) 锚点：对话推断 或 练习记忆
    anchor_big, anchor_small = (None, None)
    if conversation_summary and conversation_summary.strip():
        anchor_big, anchor_small = infer_theme_scene_from_conversation(conversation_summary)
    if not anchor_big or not anchor_small:
        anchor_big, anchor_small = get_recommended_anchor_from_history(acc)
    if (anchor_big, anchor_small) not in scene_pairs:
        anchor_big, anchor_small = (None, None)

    result: List[Dict] = []
    used_pairs: set = set()

    def learned_set(sid: str) -> set:
        return set(progress.get(sid, []))

    def add_item_for_npc(bid: str, sid: str, nid: str) -> bool:
        d = get_learn_dialogue(sid, nid)
        if not d:
            return False
        title = build_card_title(d)
        result.append({
            "big_scene_id": bid,
            "small_scene_id": sid,
            "npc_id": nid,
            "title": title,
            "learned": nid in learned_set(sid),
        })
        return True

    def pick_one_npc_for_scene(bid: str, sid: str) -> Optional[str]:
        npcs = _derive_npcs_by_small_scene(sid)
        if not npcs:
            return None
        learned = learned_set(sid)
        unlearned = [n["id"] for n in npcs if n["id"] not in learned]
        pool = unlearned if unlearned else [n["id"] for n in npcs]
        return random.choice(pool) if pool else None

    def add_one_random_for_scene(bid: str, sid: str) -> bool:
        nid = pick_one_npc_for_scene(bid, sid)
        if not nid:
            return False
        used_pairs.add((bid, sid))
        return add_item_for_npc(bid, sid, nid)

    # 2) 锚点场景：该场景下全部 NPC 各推荐一条（带 learned 标识）
    if anchor_big and anchor_small:
        used_pairs.add((anchor_big, anchor_small))
        npcs = _derive_npcs_by_small_scene(anchor_small)
        for n in npcs:
            nid = n.get("id")
            if nid:
                add_item_for_npc(anchor_big, anchor_small, nid)

    # 3) 其余场景：每场景随机 1 个，直到达到 count
    remaining = [(b, s) for (b, s) in scene_pairs if (b, s) not in used_pairs]
    random.shuffle(remaining)
    for (bid, sid) in remaining:
        if len(result) >= count:
            break
        add_one_random_for_scene(bid, sid)

    return result

# --- 场景列表（从 dialogues 推导）---

def _derive_big_scenes() -> List[Dict]:
    """从 dialogues 推导大场景，保持原有顺序"""
    order_map = {"daily": 1, "food": 2, "travel": 3, "shopping": 4, "work": 5, "social": 6}
    seen = {}
    for d in get_dialogues():
        bid = d.get("big_scene")
        if not bid:
            continue
        if bid not in seen:
            seen[bid] = {
                "id": bid,
                "name": d.get("big_scene_name", bid),
                "order": order_map.get(bid, 99)
            }
    return sorted(seen.values(), key=lambda x: x.get("order", 99))

def _derive_small_scenes_by_big(big_scene_id: str) -> List[Dict]:
    """从 dialogues 推导某大场景下的小场景"""
    order_map = {}
    seen = {}
    for d in get_dialogues():
        if d.get("big_scene") != big_scene_id:
            continue
        sid = d.get("small_scene")
        if not sid:
            continue
        if sid not in seen:
            seen[sid] = {
                "id": sid,
                "big_scene_id": big_scene_id,
                "name": d.get("small_scene_name", sid),
                "immersive_scene_id": d.get("immersive_scene_id", _to_immersive_scene_id(sid)),
                "order": len(seen) + 1
            }
    return sorted(seen.values(), key=lambda x: (x.get("order", 99), x["id"]))

def _derive_npcs_by_small_scene(small_scene_id: str) -> List[Dict]:
    """从 dialogues 推导某小场景下的 NPC（仅包含有 learn 对话的）"""
    seen = {}
    for d in get_dialogues():
        if d.get("small_scene") != small_scene_id or d.get("usage") != "learn":
            continue
        nid = d.get("npc")
        if not nid:
            continue
        if nid not in seen:
            seen[nid] = {"id": nid, "small_scene_id": small_scene_id, "name": d.get("npc_name", nid)}
    return list(seen.values())

def get_big_scenes() -> List[Dict]:
    return _derive_big_scenes()

def get_small_scenes_by_big(big_scene_id: str) -> List[Dict]:
    return _derive_small_scenes_by_big(big_scene_id)

def get_npcs_by_small_scene(small_scene_id: str) -> List[Dict]:
    return _derive_npcs_by_small_scene(small_scene_id)

def get_big_scenes_with_immersive() -> List[Dict]:
    """返回只包含至少有一个 immersive 小场景的大场景列表，每项含 image。优先读索引。"""
    idx = _load_scene_index()
    if idx:
        has_immersive_set = set(idx.get("has_immersive") or [])
        small_by_big = idx.get("small_scenes_by_big") or {}
        result = []
        for b in idx.get("big_scenes") or []:
            big_id = b.get("id")
            if not big_id:
                continue
            for s in small_by_big.get(big_id) or []:
                if (s.get("small_scene_id") or s.get("id")) in has_immersive_set:
                    result.append({**b, "image": _big_scene_image_url(big_id)})
                    break
        return result
    has_immersive = _get_scenes_with_immersive_dialogues()
    bigs = _derive_big_scenes()
    result = []
    for b in bigs:
        big_id = b.get("id")
        if not big_id:
            continue
        smalls = _derive_small_scenes_by_big(big_id)
        keep = False
        for s in smalls:
            sid = s.get("id")
            if sid and sid in has_immersive:
                keep = True
                break
        if keep:
            result.append({**b, "image": _big_scene_image_url(big_id)})
    return result

# --- 沉浸式场景列表 ---

def get_immersive_small_scenes_by_big(big_scene_id: str, account_name: Optional[str] = None) -> List[Dict]:
    """返回某大场景下、有沉浸式对话的小场景列表；每项含 can_enter、本地图 URL。优先读索引。"""
    acc = _safe_account(account_name or "")
    progress = get_npc_progress(acc)
    idx = _load_scene_index()
    if idx:
        has_immersive_set = set(idx.get("has_immersive") or [])
        smalls = (idx.get("small_scenes_by_big") or {}).get(big_scene_id) or []
        result = []
        for s in smalls:
            sid = s.get("small_scene_id") or s.get("id")
            if sid and sid in has_immersive_set:
                result.append({
                    "id": s.get("immersive_scene_id", _to_immersive_scene_id(sid)),
                    "small_scene_id": sid,
                    "title": s.get("name", sid),
                    "image": _scene_image_url(sid),
                    "can_enter": scene_can_enter(acc, sid, progress),
                })
        return result
    has_immersive = _get_scenes_with_immersive_dialogues()
    small_scenes = _derive_small_scenes_by_big(big_scene_id)
    result = []
    for s in small_scenes:
        sid = s.get("id")
        if sid and sid in has_immersive:
            result.append({
                "id": s.get("immersive_scene_id", _to_immersive_scene_id(sid)),
                "small_scene_id": sid,
                "title": s.get("name", sid),
                "image": _scene_image_url(sid),
                "can_enter": scene_can_enter(acc, sid, progress),
            })
    return result


def get_immersive_scene_list(account_name: Optional[str] = None) -> List[Dict]:
    """返回所有沉浸式场景（全展示）；每项含 can_enter、本地图 URL。优先读索引。"""
    acc = _safe_account(account_name or "")
    progress = get_npc_progress(acc)
    idx = _load_scene_index()
    if idx:
        detail_by_id = idx.get("scene_detail_by_immersive_id") or {}
        result = []
        for immersive_id, detail in detail_by_id.items():
            sid = detail.get("small_scene_id")
            if not sid:
                continue
            result.append({
                "id": immersive_id,
                "small_scene_id": sid,
                "title": detail.get("title", sid),
                "image": _scene_image_url(sid),
                "can_enter": scene_can_enter(acc, sid, progress),
            })
        return result
    has_immersive = _get_scenes_with_immersive_dialogues()
    scene_info = {}
    for d in get_dialogues():
        sid = d.get("small_scene")
        if not sid or sid not in has_immersive:
            continue
        if sid not in scene_info:
            scene_info[sid] = {
                "name": d.get("small_scene_name", sid),
                "immersive_scene_id": d.get("immersive_scene_id", _to_immersive_scene_id(sid))
            }
    result = []
    for sid, info in scene_info.items():
        result.append({
            "id": info["immersive_scene_id"],
            "small_scene_id": sid,
            "title": info["name"],
            "image": _scene_image_url(sid),
            "can_enter": scene_can_enter(acc, sid, progress),
        })
    return result

def get_immersive_scene_detail(immersive_scene_id: str, account_name: Optional[str] = None) -> Optional[Dict]:
    """返回沉浸式场景详情；每个 NPC 带 learned。优先读索引，图片用本地图。"""
    acc = _safe_account(account_name or "")
    idx = _load_scene_index()
    if idx:
        detail_by_id = idx.get("scene_detail_by_immersive_id") or {}
        detail = detail_by_id.get(immersive_scene_id)
        if not detail:
            return None
        small_scene_id = detail.get("small_scene_id")
        title = detail.get("title", small_scene_id)
        progress = get_npc_progress(acc)
        learned_set = set(progress.get(small_scene_id, []))
        valid_npcs = []
        for n in detail.get("npcs") or []:
            char = n.get("character", f"{small_scene_id}_{n['id']}")
            valid_npcs.append({
                "id": n["id"],
                "label": n.get("label", n["id"]),
                "hint": f"点我与{n.get('label', n['id'])}对话",
                "character": char,
                "learned": n["id"] in learned_set,
                "image": _npc_image_url(char),
            })
        if not valid_npcs:
            return None
        return {
            "title": title,
            "image": _scene_image_url(small_scene_id),
            "small_scene_id": small_scene_id,
            "can_enter": scene_can_enter(acc, small_scene_id, progress),
            "npcs": valid_npcs,
        }
    rev = {_to_immersive_scene_id(k): k for k in _get_scenes_with_immersive_dialogues()}
    small_scene_id = rev.get(immersive_scene_id) or immersive_scene_id
    if small_scene_id not in _get_scenes_with_immersive_dialogues():
        return None
    title = small_scene_id
    for d in get_dialogues():
        if d.get("small_scene") == small_scene_id:
            title = d.get("small_scene_name", small_scene_id)
            break
    progress = get_npc_progress(acc)
    learned_set = set(progress.get(small_scene_id, []))
    npcs = _derive_npcs_by_small_scene(small_scene_id)
    valid_npcs = []
    for n in npcs:
        if get_immersive_dialogue(small_scene_id, n["id"]):
            char = f"{small_scene_id}_{n['id']}"
            valid_npcs.append({
                "id": n["id"],
                "label": n.get("name", n["id"]),
                "hint": f"点我与{n.get('name', n['id'])}对话",
                "character": char,
                "learned": n["id"] in learned_set,
                "image": _npc_image_url(char),
            })
    if not valid_npcs:
        return None
    return {
        "title": title,
        "image": _scene_image_url(small_scene_id),
        "small_scene_id": small_scene_id,
        "can_enter": scene_can_enter(acc, small_scene_id, progress),
        "npcs": valid_npcs,
    }
