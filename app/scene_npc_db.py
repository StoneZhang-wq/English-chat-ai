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
    """强制重新加载 dialogues.json（用于配置变更后）"""
    global _DIALOGUES_CACHE
    _DIALOGUES_CACHE = None

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
    """返回已解锁的 small_scene_id 列表"""
    acc = _safe_account(account_name)
    _ensure_default_unlocks(acc)
    data = _load_json(_unlock_path(acc), {})
    return [k for k, v in data.items() if v]

def get_npc_progress(account_name: str) -> Dict[str, List[str]]:
    """返回 {small_scene_id: [npc_id, ...]} 已完成 learn 的 NPC"""
    return _load_json(_npc_progress_path(account_name), {})

def mark_npc_learned(account_name: str, small_scene_id: str, npc_id: str) -> None:
    """标记某 NPC 的 learn 已完成"""
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
    """若该小场景下所有 NPC 都已学完，则解锁；返回是否新解锁"""
    npcs_in_scene = _get_npc_ids_with_learn_in_scene(small_scene_id)
    if not npcs_in_scene:
        return False
    progress = get_npc_progress(account_name)
    learned = set(progress.get(small_scene_id, []))
    if learned >= set(npcs_in_scene):
        unlock_data = _load_json(_unlock_path(account_name), {})
        was_unlocked = unlock_data.get(small_scene_id, False)
        unlock_data[small_scene_id] = True
        _save_json(_unlock_path(account_name), unlock_data)
        return not was_unlocked
    return False

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
    """返回只包含至少有一个 immersive 小场景的大场景列表"""
    has_immersive = _get_scenes_with_immersive_dialogues()
    # 枚举所有大场景，保留那些其下存在 has_immersive 的 small_scene
    bigs = _derive_big_scenes()
    result = []
    for b in bigs:
        big_id = b.get("id")
        if not big_id:
            continue
        # 检查该大场景下是否有任何 small_scene 在 has_immersive 中
        smalls = _derive_small_scenes_by_big(big_id)
        keep = False
        for s in smalls:
            sid = s.get("id")
            if sid and sid in has_immersive:
                keep = True
                break
        if keep:
            result.append(b)
    return result

# --- 沉浸式场景列表 ---

def get_immersive_small_scenes_by_big(big_scene_id: str, account_name: Optional[str] = None) -> List[Dict]:
    """返回某大场景下、有沉浸式对话的小场景列表"""
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
                "image": f"https://placehold.co/1200x800?text={s.get('name', sid).replace(' ', '+')}"
            })
    return result


def get_immersive_scene_list(account_name: Optional[str] = None) -> List[Dict]:
    """返回可进入的沉浸式场景：从 dialogues 中有 immersive 的小场景推导"""
    has_immersive = _get_scenes_with_immersive_dialogues()
    # 需要 small_scene 的 name 和 immersive_scene_id
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
            "image": f"https://placehold.co/1200x800?text={info['name'].replace(' ', '+')}"
        })
    return result

def get_immersive_scene_detail(immersive_scene_id: str, account_name: Optional[str] = None) -> Optional[Dict]:
    """返回沉浸式场景详情：从 dialogues 推导"""
    # 反查 small_scene：immersive_scene_id 可能等于 small_scene 或 override
    rev = {_to_immersive_scene_id(k): k for k in _get_scenes_with_immersive_dialogues()}
    small_scene_id = rev.get(immersive_scene_id) or immersive_scene_id
    if small_scene_id not in _get_scenes_with_immersive_dialogues():
        return None
    # 获取场景名称
    title = small_scene_id
    immersive_id = _to_immersive_scene_id(small_scene_id)
    for d in get_dialogues():
        if d.get("small_scene") == small_scene_id:
            title = d.get("small_scene_name", small_scene_id)
            immersive_id = d.get("immersive_scene_id", immersive_id)
            break
    npcs = _derive_npcs_by_small_scene(small_scene_id)
    valid_npcs = []
    for n in npcs:
        if get_immersive_dialogue(small_scene_id, n["id"]):
            valid_npcs.append({
                "id": n["id"],
                "label": n.get("name", n["id"]),
                "hint": f"点我与{n.get('name', n['id'])}对话",
                "character": f"{small_scene_id}_{n['id']}"
            })
    if not valid_npcs:
        return None
    return {
        "title": title,
        "image": f"https://placehold.co/1200x800?text={title.replace(' ', '+')}",
        "small_scene_id": small_scene_id,
        "npcs": valid_npcs
    }
