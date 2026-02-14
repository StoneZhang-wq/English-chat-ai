"""
口语训练数据库：仅使用 data/oral_training_db.json。
提供场景列表、选卡（按 scene + difficulty + 用户 unit_practice）、Review 行、摘要推荐等。
"""
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Any

# 摘要关键词 -> scene（与 docs/ORAL_TRAINING_INTEGRATION.md 一致）
KEYWORDS_BY_SCENE = {
    "Daily Life": "日常 工作 上班 作息 时间 周末 计划 习惯 感觉 压力 生活".split(),
    "Eating Out": "吃 餐厅 点餐 外卖 做饭 饭 菜 咖啡 菜单".split(),
    "Shopping": "买 购物 逛街 商店 价格 衣服 鞋 包".split(),
}

# dialogue_id 场景缩写 -> 完整 scene 名
SCENE_ABBREV_TO_FULL = {
    "DL": "Daily Life",
    "EO": "Eating Out",
    "SH": "Shopping",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _data_dir(base_dir: str = None) -> Path:
    if base_dir is None:
        base_dir = str(_project_root())
    return Path(base_dir) / "data"


def _load_db(base_dir: str = None) -> List[Dict]:
    path = _data_dir(base_dir) / "oral_training_db.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_records(base_dir: str = None) -> List[Dict]:
    return _load_db(base_dir)


def get_unique_scenes(base_dir: str = None) -> List[str]:
    records = _load_db(base_dir)
    seen = set()
    out = []
    for r in records:
        s = r.get("scene", "")
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def get_unique_difficulties(base_dir: str = None) -> List[str]:
    records = _load_db(base_dir)
    seen = set()
    for r in records:
        d = r.get("difficulty", "")
        if d:
            seen.add(d)
    return sorted(seen)  # e.g. Difficult, Intermediate, Simple


def get_records_by_scene_difficulty(
    scene: str, difficulty: str, include_review: bool = False, base_dir: str = None
) -> List[Dict]:
    records = _load_db(base_dir)
    out = []
    for r in records:
        if r.get("scene") != scene or r.get("difficulty") != difficulty:
            continue
        if not include_review and r.get("batch") == "Review":
            continue
        out.append(r)
    return out


def get_review_record(scene: str, unit: str, base_dir: str = None) -> Optional[Dict]:
    records = _load_db(base_dir)
    for r in records:
        if r.get("scene") == scene and r.get("unit") == unit and r.get("batch") == "Review":
            return r
    return None


def get_record_by_dialogue_id(dialogue_id: str, base_dir: str = None) -> Optional[Dict]:
    records = _load_db(base_dir)
    for r in records:
        if r.get("dialogue_id") == dialogue_id:
            return r
    return None


def parse_dialogue_id(dialogue_id: str) -> Optional[Dict]:
    """解析 dialogue_id 得到 scene, unit, batch。例：DL-S-U1-A -> Daily Life, U1-Daily Routine, A"""
    if not dialogue_id or "-" not in dialogue_id:
        return None
    parts = dialogue_id.strip().split("-")
    if len(parts) < 4:
        return None
    abbrev, diff_abbrev, unit_part, batch = parts[0], parts[1], parts[2], parts[3]
    scene = SCENE_ABBREV_TO_FULL.get(abbrev.upper())
    if not scene:
        return None
    # unit 在 DB 里是 "U1-Daily Routine" 这种，dialogue_id 里是 "U1" 或 "U1-A" 等，需要从 DB 反查
    return {"scene": scene, "unit_short": unit_part, "batch": batch, "dialogue_id": dialogue_id}


def infer_unit_from_dialogue_id(dialogue_id: str, base_dir: str = None) -> Optional[str]:
    """通过 dialogue_id 在 DB 中查到对应记录的 unit 全名。"""
    r = get_record_by_dialogue_id(dialogue_id, base_dir)
    return r.get("unit") if r else None


def suggested_scene_from_summary(summary: str) -> Optional[str]:
    """根据摘要关键词返回推荐场景（与 ORAL_TRAINING_INTEGRATION 一致）。"""
    if not summary or not summary.strip():
        return None
    s = summary.strip()
    best = None
    best_count = 0
    for scene, keywords in KEYWORDS_BY_SCENE.items():
        count = sum(1 for kw in keywords if kw in s)
        if count > best_count:
            best_count = count
            best = scene
    return best


# 合并存储：场景选择次数 + 单元/批次完成情况 共用一个 JSON，键 "scene_choices" 为保留键
_SCENE_CHOICES_KEY = "scene_choices"
# unit 下用户自评「掌握了」的标记（该 unit 不再推送 B/C）
_UNIT_MASTERED_KEY = "_mastered"


def _memory_dir(base_dir: str = None) -> Path:
    if base_dir is None:
        base_dir = str(_project_root())
    return Path(base_dir) / "memory" / "accounts"


def _unit_practice_path(account_name: str, base_dir: str = None) -> Path:
    """唯一存储路径：unit_practice.json 内含 scene_choices 与各场景的 unit 完成情况。"""
    return _memory_dir(base_dir) / account_name / "unit_practice.json"


def _load_full(account_name: str, base_dir: str = None) -> Dict:
    """读取完整 JSON；若存在旧版 scene_choices.json 则合并后写入并删除旧文件。"""
    path = _unit_practice_path(account_name, base_dir)
    scene_choices_path = _memory_dir(base_dir) / account_name / "scene_choices.json"
    data = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    # 迁移：若仍有单独 scene_choices.json，合并进来并删除
    if scene_choices_path.exists():
        try:
            with open(scene_choices_path, "r", encoding="utf-8") as f:
                old_choices = json.load(f)
            if isinstance(old_choices, dict):
                existing = data.get(_SCENE_CHOICES_KEY, {})
                if isinstance(existing, dict):
                    for k, v in old_choices.items():
                        if isinstance(v, (int, float)):
                            existing[k] = existing.get(k, 0) + int(v)
                    data[_SCENE_CHOICES_KEY] = existing
                else:
                    data[_SCENE_CHOICES_KEY] = old_choices
        except Exception:
            pass
        try:
            scene_choices_path.unlink()
        except Exception:
            pass
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def _save_full(account_name: str, data: Dict, base_dir: str = None) -> None:
    path = _unit_practice_path(account_name, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_unit_practice(account_name: str, base_dir: str = None) -> Dict:
    """返回「场景 -> unit -> batch -> {completed}」视图，不含 scene_choices。"""
    full = _load_full(account_name, base_dir)
    return {k: v for k, v in full.items() if k != _SCENE_CHOICES_KEY}


def save_unit_practice(account_name: str, data: Dict, base_dir: str = None) -> None:
    """保存 unit 完成情况，保留已有 scene_choices。"""
    full = _load_full(account_name, base_dir)
    choices = full.get(_SCENE_CHOICES_KEY, {})
    if not isinstance(choices, dict):
        choices = {}
    out = {_SCENE_CHOICES_KEY: choices}
    for k, v in data.items():
        if k != _SCENE_CHOICES_KEY:
            out[k] = v
    _save_full(account_name, out, base_dir)


def load_scene_choices(account_name: str, base_dir: str = None) -> Dict[str, int]:
    """从合并文件中读取场景选择次数。"""
    full = _load_full(account_name, base_dir)
    choices = full.get(_SCENE_CHOICES_KEY, {})
    return choices if isinstance(choices, dict) else {}


def save_scene_choices(account_name: str, data: Dict[str, int], base_dir: str = None) -> None:
    """保存场景选择次数，保留已有 unit 完成情况。"""
    full = _load_full(account_name, base_dir)
    unit_data = {k: v for k, v in full.items() if k != _SCENE_CHOICES_KEY}
    full = {_SCENE_CHOICES_KEY: data, **unit_data}
    _save_full(account_name, full, base_dir)


def increment_scene_choice(account_name: str, scene: str, base_dir: str = None) -> None:
    full = _load_full(account_name, base_dir)
    choices = full.get(_SCENE_CHOICES_KEY, {})
    if not isinstance(choices, dict):
        choices = {}
    choices[scene] = choices.get(scene, 0) + 1
    full[_SCENE_CHOICES_KEY] = choices
    _save_full(account_name, full, base_dir)


def has_practiced_any_unit_in_scene(unit_practice: Dict, scene: str) -> bool:
    """该用户在该 scene 下是否练过任意 unit。"""
    scene_data = unit_practice.get(scene, {})
    for unit, batches in scene_data.items():
        if not isinstance(batches, dict):
            continue
        for batch, info in batches.items():
            if batch == _UNIT_MASTERED_KEY:
                continue
            if isinstance(info, dict) and info.get("completed"):
                return True
    return False


def get_next_batch_for_unit(unit_practice: Dict, scene: str, unit: str) -> Optional[str]:
    """
    根据 unit_practice 决定该 unit 下次应推送的批次：A -> B -> C。
    - 若用户曾自评「掌握了」该 unit（_mastered），返回 None，不再推 B/C。
    - 否则返回第一个未 completed 的批次；A/B/C 都已完成则视为默认掌握，返回 None。
    """
    scene_data = unit_practice.get(scene, {})
    unit_data = scene_data.get(unit, {})
    if unit_data.get(_UNIT_MASTERED_KEY):
        return None
    for batch in ("A", "B", "C"):
        info = unit_data.get(batch, {})
        if isinstance(info, dict) and info.get("completed"):
            continue
        return batch
    return None  # A/B/C 都已完成，默认视为 unit 掌握


def is_unit_mastered(unit_practice: Dict, scene: str, unit: str) -> bool:
    """用户自评「掌握了」该 unit，或 A/B/C 三批次都已完成，则视为掌握。"""
    scene_data = unit_practice.get(scene, {})
    unit_data = scene_data.get(unit, {})
    if unit_data.get(_UNIT_MASTERED_KEY):
        return True
    for batch in ("A", "B", "C"):
        info = unit_data.get(batch, {})
        if not (isinstance(info, dict) and info.get("completed")):
            return False
    return True


def mark_batch_completed(account_name: str, scene: str, unit: str, batch: str, base_dir: str = None) -> None:
    data = load_unit_practice(account_name, base_dir)
    if scene not in data:
        data[scene] = {}
    if unit not in data[scene]:
        data[scene][unit] = {}
    if batch not in data[scene][unit]:
        data[scene][unit][batch] = {}
    if not isinstance(data[scene][unit][batch], dict):
        data[scene][unit][batch] = {}
    data[scene][unit][batch]["completed"] = True
    save_unit_practice(account_name, data, base_dir)


def mark_unit_mastered(account_name: str, scene: str, unit: str, base_dir: str = None) -> None:
    """用户自评「掌握了」该 unit 时调用，标记后该 unit 不再推送 B/C。"""
    full = _load_full(account_name, base_dir)
    if scene not in full or full[scene] is None:
        full[scene] = {}
    if unit not in full[scene]:
        full[scene][unit] = {}
    if not isinstance(full[scene][unit], dict):
        full[scene][unit] = {}
    full[scene][unit][_UNIT_MASTERED_KEY] = True
    _save_full(account_name, full, base_dir)


def get_dialogue_record_for_user(
    scene: str,
    difficulty: str,
    account_name: str,
    base_dir: str = None,
) -> Optional[Dict]:
    """
    根据用户 unit_practice 为该用户选一条要练的记录。
    规则：先推荐「之前没掌握的 unit 的后续批次」（B 再 C），再推荐其他 unit 的 A；同优先级选该 unit 已完成批次数少的。
    """
    records = get_records_by_scene_difficulty(scene, difficulty, include_review=False, base_dir=base_dir)
    if not records:
        return None
    unit_practice = load_unit_practice(account_name, base_dir)

    # 按 unit 分组
    by_unit: Dict[str, List[Dict]] = {}
    for r in records:
        u = r.get("unit", "")
        if u not in by_unit:
            by_unit[u] = []
        by_unit[u].append(r)

    candidates = []  # (priority, total_done_count, record)
    for unit, unit_records in by_unit.items():
        next_batch = get_next_batch_for_unit(unit_practice, scene, unit)
        if next_batch is None:
            continue
        for r in unit_records:
            if r.get("batch") != next_batch:
                continue
            # 统计该 unit 已完成批次数
            unit_data = unit_practice.get(scene, {}).get(unit, {})
            total_done = sum(
                1 for b in ("A", "B", "C")
                if isinstance(unit_data.get(b), dict) and unit_data[b].get("completed")
            )
            # 优先推荐「没掌握的 unit 的后续批次」：B 优先，再 C，最后才是新 unit 的 A
            priority = 0 if next_batch == "B" else 1 if next_batch == "C" else 2
            candidates.append((priority, total_done, r))
            break

    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]


def get_scene_options_for_user(
    account_name: str,
    suggested_scene: Optional[str] = None,
    base_dir: str = None,
) -> Dict[str, Any]:
    """
    返回场景列表：recommended（最多1个）, frequent（常选）, new（未学过）。
    每条 { scene, label, choice_count? }
    """
    scenes = get_unique_scenes(base_dir)
    scene_choices = load_scene_choices(account_name, base_dir)
    unit_practice = load_unit_practice(account_name, base_dir)

    # 未学过：该 scene 下没有任何 unit 的任意 batch completed
    def is_new(sc: str) -> bool:
        return not has_practiced_any_unit_in_scene(unit_practice, sc)

    options = []
    used = set()

    if suggested_scene and suggested_scene in scenes:
        options.append({"scene": suggested_scene, "label": "recommended"})
        used.add(suggested_scene)

    # frequent: 按 choice_count 降序，取前 3，排除已用
    sorted_by_choice = sorted(
        [s for s in scenes if s not in used],
        key=lambda s: scene_choices.get(s, 0),
        reverse=True,
    )
    for s in sorted_by_choice[:3]:
        options.append({
            "scene": s,
            "label": "frequent",
            "choice_count": scene_choices.get(s, 0),
        })
        used.add(s)

    # new: 未学过的里取 2 个，排除已用
    new_list = [s for s in scenes if s not in used and is_new(s)]
    for s in new_list[:2]:
        options.append({"scene": s, "label": "new"})
        used.add(s)

    return {
        "suggested_scene": suggested_scene,
        "options": options,
    }
