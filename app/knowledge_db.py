"""
知识点数据库管理模块（语块/句型：文件或 MySQL 二选一）
- 默认使用文件后端（data/*.json），无需 MySQL；设置 CHUNK_BACKEND=mysql 时使用 MySQL。
- 数据：场景、语块、语块-场景关联、用户场景权重、用户语块学习进度。
"""
from pathlib import Path
from typing import List, Dict, Optional

# 默认用文件后端（无数据库）；CHUNK_BACKEND=mysql 时用 MySQL
def _chunk_backend(base_dir: str):
    import os
    if os.environ.get("CHUNK_BACKEND", "").strip().lower() == "mysql":
        from .chunk_db import ChunkDatabase
        return ChunkDatabase(base_dir)
    from .chunk_file import ChunkDatabaseFile
    return ChunkDatabaseFile(base_dir)

from .chunk_db import (
    CATEGORY_CHUNK,
    CATEGORY_PATTERN,
    DIFFICULTY_MIN,
    DIFFICULTY_MAX,
)

# 旧难度等级到新难度枚举的映射（1=最低，2=中等，3=最高）
LEVEL_ORDER = ["beginner", "elementary", "pre_intermediate", "intermediate", "upper_intermediate", "advanced"]


def _user_level_to_difficulty(user_level: str) -> int:
    if user_level in ("beginner", "elementary"):
        return 1
    if user_level in ("pre_intermediate", "intermediate"):
        return 2
    if user_level in ("upper_intermediate", "advanced"):
        return 3
    return 1


def _category_to_type_name(category: int) -> str:
    return "语块" if category == CATEGORY_CHUNK else "句型"


def _type_name_to_category(knowledge_type: str) -> int:
    if knowledge_type in ("单词", "词组", "俚语", "语块"):
        return CATEGORY_CHUNK
    if knowledge_type in ("语法", "句子", "句型"):
        return CATEGORY_PATTERN
    return CATEGORY_CHUNK


class KnowledgeDatabase:
    """
    知识点数据库：对外保持原有 API，内部委托给文件后端（默认）或 MySQL。
    用户专属数据：场景权重、语块学习进度（存于 memory/accounts/<user_id>/ 或 MySQL）。
    """

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self._chunk_db = _chunk_backend(str(self.base_dir))

    def init_user_progress(self, user_id: str) -> None:
        """初始化用户专属数据：为所有场景在 user_scene_weight 中插入 weight=0。"""
        self._chunk_db.init_user_scene_weights(user_id)

    def get_available_scenes(self) -> List[Dict]:
        """返回所有可用场景（一级/二级/三级 + label_id），兼容 scene_primary / scene_secondary。"""
        return self._chunk_db.get_available_scenes()

    def get_default_scene(self) -> Optional[Dict]:
        """返回一个默认场景（第一个可用场景），供未选择场景时自动使用。"""
        scenes = self._chunk_db.get_available_scenes()
        return scenes[0] if scenes else None

    def get_second_level_options(self, first_scene: str, limit: int = 3) -> List[Dict]:
        """根据一级场景返回最多 limit 个二级选项，供用户选一个；每选项含该二级下所有三级的 label_ids。"""
        return self._chunk_db.get_second_level_options(first_scene.strip(), limit=limit)

    def get_label_id_by_scenes(
        self,
        scene_primary: str,
        scene_secondary: str,
        scene_tertiary: Optional[str] = None,
    ) -> Optional[int]:
        """根据一级/二级/三级场景名解析 label_id，供 select-scene 与 generate 使用。"""
        return self._chunk_db.get_label_id_by_scenes(
            scene_primary,
            scene_secondary,
            scene_tertiary,
        )

    def get_recommended_knowledge(
        self,
        user_id: str,
        user_level: str,
        selected_scene_secondary: Optional[str] = None,
        selected_label_id: Optional[int] = None,
        scene_primary: Optional[str] = None,
        scene_secondary: Optional[str] = None,
    ) -> List[Dict]:
        """
        按场景层级优先级推荐语块/句型。
        返回格式兼容旧逻辑：列表元素含 英文、类型(语块/句型)、知识点ID(chunk_id)、难度 等。
        """
        difficulty_max = _user_level_to_difficulty(user_level)
        # 若同时传了一级+二级，则用该二级下所有三级的语块/句型；否则用 selected_label_id 或按 scene 解析的 label_id
        use_first_second = bool(scene_primary and scene_secondary)
        label_id = None if use_first_second else (selected_label_id or (self._chunk_db.get_label_id_by_scenes(scene_primary or "", scene_secondary or "") if (scene_primary and scene_secondary) else None))

        chunks = self._chunk_db.get_recommended_chunks(
            user_id=user_id,
            user_difficulty_max=difficulty_max,
            selected_label_id=label_id,
            first_scene=scene_primary if use_first_second else None,
            second_scene=scene_secondary if use_first_second else None,
            limit=30,
            prefer_wrong_first=True,
        )
        return [
            {
                "英文": c["chunk"],
                "类型": _category_to_type_name(c["category"]),
                "知识点ID": str(c["chunk_id"]),
                "难度": c["difficulty"],
                "chunk_id": c["chunk_id"],
                "category": c["category"],
            }
            for c in chunks
        ]

    def update_learning_progress(
        self,
        user_id: str,
        knowledge_id: str,
        is_correct: bool,
        knowledge_info: Optional[Dict] = None,
    ) -> None:
        """更新用户语块学习进度（知识点ID 即 chunk_id）。"""
        try:
            cid = int(knowledge_id)
        except (TypeError, ValueError):
            return
        self._chunk_db.update_chunk_progress(user_id, cid, is_correct)

    def update_scene_preference(self, user_id: str, scene_primary: str, scene_secondary: str) -> None:
        """练习结束后更新该场景的用户权重（小幅增加）。"""
        label_id = self._chunk_db.get_label_id_by_scenes(scene_primary, scene_secondary)
        if label_id is not None:
            self._chunk_db.update_scene_weight(user_id, label_id, weight_delta=0.3)

    def increment_scene_choice(self, user_id: str, scene_primary: str, scene_secondary: str) -> None:
        """用户手动选择场景时调用；若传入的是 label_id，请使用 increment_scene_choice_by_label。"""
        label_id = self._chunk_db.get_label_id_by_scenes(scene_primary, scene_secondary)
        if label_id is not None:
            self._chunk_db.increment_scene_choice(user_id, label_id)

    def increment_scene_choice_by_label(self, user_id: str, label_id: int) -> None:
        """用户手动选择场景时调用（按 label_id）。"""
        self._chunk_db.increment_scene_choice(user_id, label_id)

    def add_knowledge_to_master(
        self,
        english: str,
        knowledge_type: str,
        scene_primary: Optional[str] = None,
        scene_secondary: Optional[str] = None,
        difficulty: str = "beginner",
        chinese_content: Optional[str] = None,
    ) -> Dict:
        """
        将新语块/句型加入 chunk_core 并绑定场景。
        返回格式兼容旧逻辑：含 知识点ID(chunk_id)、英文、类型 等。
        """
        category = _type_name_to_category(knowledge_type)
        difficulty_int = _user_level_to_difficulty(difficulty)
        label_id = None
        if scene_primary and scene_secondary:
            label_id = self._chunk_db.get_label_id_by_scenes(scene_primary, scene_secondary)
        if label_id is None:
            # 无场景时使用默认场景（需存在一条 scene_label）
            scenes = self._chunk_db.get_available_scenes()
            if scenes:
                label_id = scenes[0].get("label_id")
            else:
                raise ValueError("无可用场景，无法添加知识点；请先在 scene_label 中创建场景")
        row = self._chunk_db.add_chunk(
            chunk_text=english.strip(),
            category=category,
            difficulty=difficulty_int,
            label_id=label_id,
            weight=0.0,
        )
        return {
            "知识点ID": str(row["chunk_id"]),
            "英文": row["chunk"],
            "类型": _category_to_type_name(row["category"]),
            "难度": row["difficulty"],
            "chunk_id": row["chunk_id"],
        }

    def find_chunk_by_text(self, text: str, category: Optional[int] = None) -> Optional[Dict]:
        """按语块/句型原文查找，用于练习保存时匹配。"""
        return self._chunk_db.find_chunk_by_text(text, category=category)
