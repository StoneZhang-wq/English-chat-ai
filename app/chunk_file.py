"""
语块/场景文件后端：用 JSON 文件替代 MySQL，无需安装数据库。
- data/scenes.json: 场景（一级/二级/三级）
- data/chunks.json: 语块/句型
- data/chunk_scene_mapping.json: 语块-场景多对多
- memory/accounts/<user_id>/scene_weights.json: 用户场景权重
- memory/accounts/<user_id>/chunk_progress.json: 用户语块学习进度
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any

from .chunk_db import (
    DIFFICULTY_MIN,
    DIFFICULTY_MAX,
    CATEGORY_CHUNK,
    CATEGORY_PATTERN,
)

# 从 chunk_db 导出，供 knowledge_db 使用
__all__ = ["ChunkDatabaseFile", "CATEGORY_CHUNK", "CATEGORY_PATTERN", "DIFFICULTY_MIN", "DIFFICULTY_MAX"]


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default if default is not None else []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else []


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ChunkDatabaseFile:
    """
    语块/场景文件后端：与 ChunkDatabase 相同接口，数据存 JSON。
    卡片生成优先级：场景权重 → 同二级/一级扩展 → 语块 weight / difficulty / last_correct。
    """

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self._data_dir = self.base_dir / "data"
        self._memory_dir = self.base_dir / "memory" / "accounts"

    def _scenes_path(self) -> Path:
        return self._data_dir / "scenes.json"

    def _chunks_path(self) -> Path:
        return self._data_dir / "chunks.json"

    def _mapping_path(self) -> Path:
        return self._data_dir / "chunk_scene_mapping.json"

    def _user_scene_weights_path(self, user_id: str) -> Path:
        return self._memory_dir / user_id / "scene_weights.json"

    def _user_chunk_progress_path(self, user_id: str) -> Path:
        return self._memory_dir / user_id / "chunk_progress.json"

    def _load_scenes(self) -> List[Dict]:
        return _load_json(self._scenes_path(), [])

    def _load_chunks(self) -> List[Dict]:
        return _load_json(self._chunks_path(), [])

    def _load_mapping(self) -> List[Dict]:
        return _load_json(self._mapping_path(), [])

    def _load_user_scene_weights(self, user_id: str) -> Dict[int, float]:
        data = _load_json(self._user_scene_weights_path(user_id), {})
        return {int(k): float(v) for k, v in data.items()}

    def _save_user_scene_weights(self, user_id: str, data: Dict[int, float]) -> None:
        _save_json(self._user_scene_weights_path(user_id), {str(k): v for k, v in data.items()})

    def _load_user_chunk_progress(self, user_id: str) -> Dict[int, Dict]:
        data = _load_json(self._user_chunk_progress_path(user_id), {})
        return {int(k): v for k, v in data.items()}

    def _save_user_chunk_progress(self, user_id: str, data: Dict[int, Dict]) -> None:
        _save_json(self._user_chunk_progress_path(user_id), {str(k): v for k, v in data.items()})

    def _get_scene_weight(self, user_id: Optional[str], label_id: int, scenes_by_id: Dict[int, Dict]) -> float:
        if user_id:
            weights = self._load_user_scene_weights(user_id)
            if label_id in weights:
                return weights[label_id]
        s = scenes_by_id.get(label_id)
        return float(s["weight"]) if s else 0.0

    def get_all_labels_with_weight(self, user_id: Optional[str]) -> List[Dict]:
        scenes = self._load_scenes()
        if not scenes:
            return []
        weights = self._load_user_scene_weights(user_id or "") if user_id else {}
        result = []
        for s in scenes:
            row = dict(s)
            row["weight"] = weights.get(s["label_id"], float(s.get("weight", 0)))
            result.append(row)
        result.sort(key=lambda r: (-float(r["weight"]), r["first_scene"], r["second_scene"], r["third_scene"]))
        return result

    def get_ordered_label_ids(
        self,
        user_id: Optional[str],
        selected_label_id: Optional[int] = None,
    ) -> List[int]:
        rows = self.get_all_labels_with_weight(user_id)
        if not rows:
            return []
        by_id = {r["label_id"]: r for r in rows}
        if selected_label_id and selected_label_id in by_id:
            start = by_id[selected_label_id]
        else:
            start = max(rows, key=lambda r: (float(r["weight"]), r["first_scene"], r["second_scene"], r["third_scene"]))
        first_scene = start["first_scene"]
        second_scene = start["second_scene"]
        label_id_start = start["label_id"]
        same_second = [r for r in rows if r["first_scene"] == first_scene and r["second_scene"] == second_scene]
        same_first_other = [r for r in rows if r["first_scene"] == first_scene and r["second_scene"] != second_scene]
        rest = [r for r in rows if r["first_scene"] != first_scene]
        same_second_rest = [r for r in same_second if r["label_id"] != label_id_start]
        same_second_rest.sort(key=lambda r: (-float(r["weight"]), r["third_scene"]))
        same_second_ordered = [start] + same_second_rest
        same_first_other.sort(key=lambda r: (r["second_scene"], -float(r["weight"]), r["third_scene"]))
        rest.sort(key=lambda r: (r["first_scene"], r["second_scene"], -float(r["weight"]), r["third_scene"]))
        ordered = [r["label_id"] for r in same_second_ordered] + [r["label_id"] for r in same_first_other] + [r["label_id"] for r in rest]
        return ordered

    def _get_chunks_for_labels(
        self,
        label_ids: List[int],
        user_id: Optional[str],
        user_difficulty_max: int,
        limit: int,
        prefer_wrong_first: bool = True,
    ) -> List[Dict]:
        chunks = self._load_chunks()
        mapping = self._load_mapping()
        mapping_by_label: Dict[int, List[int]] = {}
        for m in mapping:
            lid = int(m["label_id"])
            cid = int(m["chunk_id"])
            if lid not in mapping_by_label:
                mapping_by_label[lid] = []
            mapping_by_label[lid].append(cid)
        chunks_by_id = {int(c["chunk_id"]): c for c in chunks}
        progress = self._load_user_chunk_progress(user_id or "") if user_id else {}
        result = []
        seen = set()
        for label_id in label_ids:
            if len(result) >= limit:
                break
            cids = mapping_by_label.get(label_id, [])
            rows = []
            for cid in cids:
                c = chunks_by_id.get(cid)
                if not c or c["difficulty"] > user_difficulty_max:
                    continue
                row = dict(c)
                p = progress.get(cid, {})
                row["last_correct"] = p.get("last_correct", row.get("last_correct", 1))
                row["learn_count"] = p.get("learn_count", row.get("learn_count", 0))
                rows.append(row)
            rows.sort(key=lambda r: (-float(r.get("weight", 0)), r["difficulty"], r["last_correct"]))
            for r in rows:
                cid = r["chunk_id"]
                if cid in seen:
                    continue
                seen.add(cid)
                result.append({"chunk_id": cid, "chunk": r["chunk"], "difficulty": r["difficulty"], "category": r["category"], "weight": r.get("weight", 0), "last_correct": r["last_correct"], "learn_count": r["learn_count"]})
                if len(result) >= limit:
                    break
        return result

    def get_recommended_chunks(
        self,
        user_id: Optional[str] = None,
        user_difficulty_max: int = 3,
        selected_label_id: Optional[int] = None,
        first_scene: Optional[str] = None,
        second_scene: Optional[str] = None,
        limit: int = 20,
        prefer_wrong_first: bool = True,
    ) -> List[Dict]:
        if user_id:
            self.init_user_scene_weights(user_id)
        if first_scene and second_scene:
            opts = self.get_second_level_options(first_scene.strip(), limit=100)
            opt = next((o for o in opts if (o.get("second_scene") or "").strip() == second_scene.strip()), None)
            ordered_label_ids = opt.get("label_ids", []) if opt else []
        else:
            ordered_label_ids = self.get_ordered_label_ids(user_id, selected_label_id)
        return self._get_chunks_for_labels(ordered_label_ids, user_id, user_difficulty_max, limit, prefer_wrong_first)

    def get_second_level_options(self, first_scene: str, limit: int = 3) -> List[Dict]:
        scenes = self._load_scenes()
        first_scene = first_scene.strip()
        by_second: Dict[str, List[int]] = {}
        for s in scenes:
            if s.get("first_scene") != first_scene:
                continue
            sec = s.get("second_scene", "")
            if sec not in by_second:
                by_second[sec] = []
            by_second[sec].append(int(s["label_id"]))
        result = []
        for i, (second_scene, label_ids) in enumerate(sorted(by_second.items())):
            if i >= limit:
                break
            result.append({
                "first_scene": first_scene,
                "second_scene": second_scene,
                "label_ids": label_ids,
                "scene_primary": first_scene,
                "scene_secondary": second_scene,
            })
        return result

    def get_available_scenes(self) -> List[Dict]:
        scenes = self._load_scenes()
        return [
            {
                "label_id": r["label_id"],
                "first_scene": r["first_scene"],
                "second_scene": r["second_scene"],
                "third_scene": r["third_scene"],
                "scene_primary": r["first_scene"],
                "scene_secondary": r["second_scene"],
                "scene_tertiary": r["third_scene"],
            }
            for r in scenes
        ]

    def update_chunk_progress(self, user_id: str, chunk_id: int, is_correct: bool) -> None:
        progress = self._load_user_chunk_progress(user_id)
        p = progress.get(chunk_id, {"learn_count": 0, "correct_count": 0, "last_correct": 1})
        p["learn_count"] = p.get("learn_count", 0) + 1
        p["correct_count"] = p.get("correct_count", 0) + (1 if is_correct else 0)
        p["last_correct"] = 1 if is_correct else 0
        progress[chunk_id] = p
        self._save_user_chunk_progress(user_id, progress)

    def update_scene_weight(
        self,
        user_id: str,
        label_id: int,
        weight_delta: Optional[float] = None,
        weight_absolute: Optional[float] = None,
    ) -> None:
        weights = self._load_user_scene_weights(user_id)
        if weight_absolute is not None:
            weights[label_id] = weight_absolute
        else:
            weights[label_id] = weights.get(label_id, 0.0) + (weight_delta or 0.0)
        self._save_user_scene_weights(user_id, weights)

    def increment_scene_choice(self, user_id: str, label_id: int, choice_weight_increment: float = 0.5) -> None:
        self.update_scene_weight(user_id, label_id, weight_delta=choice_weight_increment)

    def init_user_scene_weights(self, user_id: str) -> None:
        scenes = self._load_scenes()
        weights = self._load_user_scene_weights(user_id)
        for s in scenes:
            lid = s["label_id"]
            if lid not in weights:
                weights[lid] = 0.0
        self._save_user_scene_weights(user_id, weights)

    def get_label_id_by_scenes(
        self,
        first_scene: str,
        second_scene: str,
        third_scene: Optional[str] = None,
    ) -> Optional[int]:
        scenes = self._load_scenes()
        first_scene = first_scene.strip()
        second_scene = second_scene.strip()
        for s in scenes:
            if s.get("first_scene") != first_scene or s.get("second_scene") != second_scene:
                continue
            if third_scene and s.get("third_scene") != third_scene.strip():
                continue
            return int(s["label_id"])
        return None

    def find_chunk_by_text(self, text: str, category: Optional[int] = None) -> Optional[Dict]:
        chunks = self._load_chunks()
        key = text.strip().lower()
        for c in chunks:
            if c.get("chunk", "").strip().lower() != key:
                continue
            if category is not None and c.get("category") != category:
                continue
            return {"chunk_id": c["chunk_id"], "chunk": c["chunk"], "difficulty": c["difficulty"], "category": c["category"], "weight": c.get("weight", 0)}
        return None

    def add_chunk(
        self,
        chunk_text: str,
        category: int,
        difficulty: int,
        label_id: int,
        weight: float = 0.0,
    ) -> Dict:
        chunks = self._load_chunks()
        mapping = self._load_mapping()
        chunk_text = chunk_text.strip()
        key = chunk_text.lower()
        for c in chunks:
            if c.get("chunk", "").strip().lower() == key and c.get("category") == category:
                cid = c["chunk_id"]
                if not any(m.get("chunk_id") == cid and m.get("label_id") == label_id for m in mapping):
                    mapping.append({"chunk_id": cid, "label_id": label_id})
                    _save_json(self._mapping_path(), mapping)
                return {"chunk_id": cid, "chunk": c["chunk"], "difficulty": c["difficulty"], "category": c["category"], "weight": c.get("weight", 0)}
        next_id = max((c["chunk_id"] for c in chunks), default=0) + 1
        new_chunk = {
            "chunk_id": next_id,
            "chunk": chunk_text,
            "difficulty": difficulty,
            "category": category,
            "learn_count": 0,
            "correct_count": 0,
            "last_correct": 1,
            "weight": weight,
        }
        chunks.append(new_chunk)
        mapping.append({"chunk_id": next_id, "label_id": label_id})
        _save_json(self._chunks_path(), chunks)
        _save_json(self._mapping_path(), mapping)
        return {"chunk_id": next_id, "chunk": chunk_text, "difficulty": difficulty, "category": category, "weight": weight}

    def get_user_chunk_progress(self, user_id: str) -> List[Dict]:
        progress = self._load_user_chunk_progress(user_id)
        chunks = self._load_chunks()
        chunks_by_id = {c["chunk_id"]: c for c in chunks}
        result = []
        for cid, p in progress.items():
            c = chunks_by_id.get(cid)
            if not c:
                continue
            result.append({
                "chunk_id": cid,
                "learn_count": p.get("learn_count", 0),
                "correct_count": p.get("correct_count", 0),
                "last_correct": p.get("last_correct", 1),
                "chunk": c["chunk"],
                "category": c["category"],
                "difficulty": c["difficulty"],
            })
        result.sort(key=lambda r: -r.get("learn_count", 0))
        return result
