"""
语块/句型数据库模块（MySQL）
- chunk_core: 语块/句型核心表（语块含词组/单词/俚语，句型含语法/句子）
- scene_label: 场景标签表（一级/二级/三级场景 + 权重）
- chunk_scene_mapping: 语块-场景多对多
- user_scene_weight: 用户场景权重（多用户）
- user_chunk_progress: 用户语块学习进度（多用户）

卡片生成优先级：先按场景权重（三级→二级→一级层级），再按语块 weight / difficulty / last_correct。
"""
from __future__ import annotations

import os
from typing import List, Dict, Optional, Any

# 难度枚举：1=最低，2=中等，3=最高
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 3

# 类型枚举：1=语块，2=句型
CATEGORY_CHUNK = 1
CATEGORY_PATTERN = 2


def _get_db_config() -> Dict[str, Any]:
    """从环境变量读取 MySQL 配置"""
    return {
        "host": os.environ.get("CHUNK_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("CHUNK_DB_PORT", "3306")),
        "user": os.environ.get("CHUNK_DB_USER", "root"),
        "password": os.environ.get("CHUNK_DB_PASSWORD", ""),
        "database": os.environ.get("CHUNK_DB_NAME", "english_chunk"),
        "charset": "utf8mb4",
        "cursorclass": None,  # 使用 dict cursor 需在 connect 时指定
    }


def _get_connection():
    """获取 MySQL 连接（需安装 pymysql: pip install pymysql）"""
    try:
        import pymysql
        from pymysql.cursors import DictCursor
    except ImportError:
        raise ImportError("使用语块数据库需要安装 pymysql: pip install pymysql")
    cfg = _get_db_config()
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset=cfg["charset"],
        cursorclass=DictCursor,
    )


class ChunkDatabase:
    """
    语块/句型数据库：卡片生成优先级逻辑
    - 场景层级优先级：权重最高的三级场景 → 同二级下其他三级 → 同一级下其他二级（及下属三级）
    - 支持用户手动切换至任意场景后，按新场景的「三级→二级→一级」层级生成
    - 同一场景下语块按 weight 二次排序，兼顾 difficulty、last_correct（如上次错误优先复现）
    """

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir

    def _get_scene_weight(self, conn, user_id: Optional[str], label_id: int) -> float:
        """获取场景权重：优先 user_scene_weight，否则 scene_label.weight"""
        with conn.cursor() as cur:
            if user_id:
                cur.execute(
                    "SELECT weight FROM user_scene_weight WHERE user_id = %s AND label_id = %s",
                    (user_id, label_id),
                )
                row = cur.fetchone()
                if row is not None:
                    return float(row["weight"])
            cur.execute("SELECT weight FROM scene_label WHERE label_id = %s", (label_id,))
            row = cur.fetchone()
            return float(row["weight"]) if row else 0.0

    def get_all_labels_with_weight(self, conn, user_id: Optional[str]) -> List[Dict]:
        """获取所有场景标签及权重（用户权重优先）"""
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.label_id, s.first_scene, s.second_scene, s.third_scene,
                       COALESCE(u.weight, s.weight) AS weight
                FROM scene_label s
                LEFT JOIN user_scene_weight u ON u.label_id = s.label_id AND u.user_id = %s
                ORDER BY COALESCE(u.weight, s.weight) DESC, s.first_scene, s.second_scene, s.third_scene
                """,
                (user_id or "",),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_ordered_label_ids(
        self,
        conn,
        user_id: Optional[str],
        selected_label_id: Optional[int] = None,
    ) -> List[int]:
        """
        按业务层级优先级返回 label_id 顺序：
        1) 若指定 selected_label_id：以该三级场景为起点，同二级下其他三级 → 同一级下其他二级（及下属三级）→ 其余
        2) 否则：以权重最高的三级场景为起点，同上
        """
        rows = self.get_all_labels_with_weight(conn, user_id)
        if not rows:
            return []

        by_id = {r["label_id"]: r for r in rows}
        # 确定起点 label
        if selected_label_id and selected_label_id in by_id:
            start = by_id[selected_label_id]
        else:
            start = max(rows, key=lambda r: (float(r["weight"]), r["first_scene"], r["second_scene"], r["third_scene"]))

        first_scene = start["first_scene"]
        second_scene = start["second_scene"]
        label_id_start = start["label_id"]

        # 分组：同(first, second)为“同二级”，同 first 为“同一级”
        same_second = [r for r in rows if r["first_scene"] == first_scene and r["second_scene"] == second_scene]
        same_first_other_second = [
            r for r in rows
            if r["first_scene"] == first_scene and r["second_scene"] != second_scene
        ]
        rest = [r for r in rows if r["first_scene"] != first_scene]

        # 同二级内：起点排最前，其余按权重降序
        same_second_rest = [r for r in same_second if r["label_id"] != label_id_start]
        same_second_rest.sort(key=lambda r: (-float(r["weight"]), r["third_scene"]))
        same_second_ordered = [start] + same_second_rest

        # 同一级其他二级：按二级名、权重、三级名排序
        same_first_other_second.sort(
            key=lambda r: (r["second_scene"], -float(r["weight"]), r["third_scene"]),
        )
        rest.sort(key=lambda r: (r["first_scene"], r["second_scene"], -float(r["weight"]), r["third_scene"]))

        ordered = [r["label_id"] for r in same_second_ordered] + [r["label_id"] for r in same_first_other_second] + [r["label_id"] for r in rest]
        return ordered

    def get_chunks_for_labels(
        self,
        conn,
        label_ids: List[int],
        user_id: Optional[str],
        user_difficulty_max: int,
        limit: int,
        prefer_wrong_first: bool = True,
    ) -> List[Dict]:
        """
        按 label 顺序，从每个 label 下取语块/句型，直到凑满 limit。
        同一场景内排序：chunk_core.weight DESC, difficulty ASC, last_correct ASC（错误优先）。
        难度过滤：只取 difficulty <= user_difficulty_max。
        """
        result = []
        seen_chunk_ids = set()

        for label_id in label_ids:
            if len(result) >= limit:
                break
            with conn.cursor() as cur:
                # 多用户时用 user_chunk_progress 的 last_correct；单用户可用 chunk_core 的 last_correct
                if user_id:
                    cur.execute(
                        """
                        SELECT c.chunk_id, c.chunk, c.difficulty, c.category, c.weight,
                               COALESCE(p.last_correct, 1) AS last_correct,
                               COALESCE(p.learn_count, 0) AS learn_count
                        FROM chunk_core c
                        INNER JOIN chunk_scene_mapping m ON m.chunk_id = c.chunk_id AND m.label_id = %s
                        LEFT JOIN user_chunk_progress p ON p.chunk_id = c.chunk_id AND p.user_id = %s
                        WHERE c.difficulty <= %s
                        ORDER BY c.weight DESC, c.difficulty ASC, COALESCE(p.last_correct, 1) ASC
                        """,
                        (label_id, user_id, user_difficulty_max),
                    )
                else:
                    cur.execute(
                        """
                        SELECT c.chunk_id, c.chunk, c.difficulty, c.category, c.weight, c.last_correct
                        FROM chunk_core c
                        INNER JOIN chunk_scene_mapping m ON m.chunk_id = c.chunk_id AND m.label_id = %s
                        WHERE c.difficulty <= %s
                        ORDER BY c.weight DESC, c.difficulty ASC, c.last_correct ASC
                        """,
                        (label_id, user_difficulty_max),
                    )
                rows = cur.fetchall()
            for r in rows:
                cid = r["chunk_id"]
                if cid in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(cid)
                result.append(dict(r))
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
        """
        卡片生成核心接口：按场景层级优先级 + 同场景内 weight/difficulty/last_correct 返回推荐语块/句型。
        - user_id: 多用户时传入，用于场景权重与学习进度
        - user_difficulty_max: 难度上限（1/2/3），只推荐 difficulty <= 该值
        - selected_label_id: 用户手动选择的场景（三级 label_id），为 None 则按权重最高的三级场景为起点
        - first_scene + second_scene: 用户选了一级+二级时，用该二级下所有三级的语块/句型生成卡片（与 selected_label_id 二选一）
        - limit: 最多返回条数
        """
        # 懒同步：确保该用户对当前所有场景都有 user_scene_weight 行（新增场景后首次推荐时补全）
        if user_id:
            self.init_user_scene_weights(user_id)
        conn = _get_connection()
        try:
            if first_scene and second_scene:
                # 一级+二级已定：取该二级下所有三级的 label_id，用这些语块生成卡片
                opts = self.get_second_level_options(first_scene.strip(), limit=100)
                opt = next((o for o in opts if (o.get("second_scene") or "").strip() == second_scene.strip()), None)
                ordered_label_ids = (opt["label_ids"] if opt else [])
            else:
                ordered_label_ids = self.get_ordered_label_ids(conn, user_id, selected_label_id)
            chunks = self.get_chunks_for_labels(
                conn,
                ordered_label_ids,
                user_id,
                user_difficulty_max,
                limit,
                prefer_wrong_first=prefer_wrong_first,
            )
            return chunks
        finally:
            conn.close()

    def get_second_level_options(self, first_scene: str, limit: int = 3) -> List[Dict]:
        """
        根据一级场景返回最多 limit 个二级选项，供用户选一个。
        每个选项包含该 (一级, 二级) 下所有三级的 label_id，用于后续生成卡片。
        返回格式：[{"first_scene", "second_scene", "label_ids": [id1, id2, ...]}, ...]
        """
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT label_id, first_scene, second_scene, third_scene
                       FROM scene_label WHERE first_scene = %s ORDER BY second_scene, third_scene""",
                    (first_scene.strip(),),
                )
                rows = cur.fetchall()
            # 按 second_scene 分组，每组收集所有 label_id
            by_second: Dict[str, List[int]] = {}
            for r in rows:
                sec = r["second_scene"]
                if sec not in by_second:
                    by_second[sec] = []
                by_second[sec].append(int(r["label_id"]))
            # 取前 limit 个二级
            result = []
            for i, (second_scene, label_ids) in enumerate(by_second.items()):
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
        finally:
            conn.close()

    def get_available_scenes(self) -> List[Dict]:
        """
        返回所有可用场景（层级：一级/二级/三级），供前端选择与手动切换。
        返回格式：[{"label_id", "first_scene", "second_scene", "third_scene"}, ...]
        """
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT label_id, first_scene, second_scene, third_scene FROM scene_label ORDER BY first_scene, second_scene, third_scene"
                )
                rows = cur.fetchall()
            return [
                {
                    "label_id": r["label_id"],
                    "first_scene": r["first_scene"],
                    "second_scene": r["second_scene"],
                    "third_scene": r["third_scene"],
                    # 兼容旧前端字段名
                    "scene_primary": r["first_scene"],
                    "scene_secondary": r["second_scene"],
                    "scene_tertiary": r["third_scene"],
                }
                for r in rows
            ]
        finally:
            conn.close()

    def update_chunk_progress(self, user_id: str, chunk_id: int, is_correct: bool) -> None:
        """更新用户语块学习进度（练习后调用）"""
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                inc_correct = 1 if is_correct else 0
                last_ok = 1 if is_correct else 0
                cur.execute(
                    """
                    INSERT INTO user_chunk_progress (user_id, chunk_id, learn_count, correct_count, last_correct, last_learned_at)
                    VALUES (%s, %s, 1, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                        learn_count = learn_count + 1,
                        correct_count = correct_count + %s,
                        last_correct = %s,
                        last_learned_at = NOW()
                    """,
                    (user_id, chunk_id, inc_correct, last_ok, inc_correct, last_ok),
                )
            conn.commit()
        finally:
            conn.close()

    def update_scene_weight(self, user_id: str, label_id: int, weight_delta: Optional[float] = None, weight_absolute: Optional[float] = None) -> None:
        """
        更新用户在某场景下的兴趣权重。
        - weight_delta: 在原有基础上增加（可为负）
        - weight_absolute: 直接设为该值（与 weight_delta 二选一）
        """
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                if weight_absolute is not None:
                    cur.execute(
                        """
                        INSERT INTO user_scene_weight (user_id, label_id, weight) VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE weight = %s
                        """,
                        (user_id, label_id, weight_absolute, weight_absolute),
                    )
                else:
                    cur.execute("SELECT weight FROM user_scene_weight WHERE user_id = %s AND label_id = %s", (user_id, label_id))
                    row = cur.fetchone()
                    current = float(row["weight"]) if row else 0.0
                    cur.execute(
                        """
                        INSERT INTO user_scene_weight (user_id, label_id, weight) VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE weight = weight + %s
                        """,
                        (user_id, label_id, current + (weight_delta or 0), weight_delta or 0),
                    )
            conn.commit()
        finally:
            conn.close()

    def increment_scene_choice(self, user_id: str, label_id: int, choice_weight_increment: float = 0.5) -> None:
        """用户手动选择某场景时调用，增加该场景权重"""
        self.update_scene_weight(user_id, label_id, weight_delta=choice_weight_increment)

    # ---------- 用户专属数据表逻辑 ----------

    def init_user_scene_weights(self, user_id: str) -> None:
        """
        为新用户初始化场景权重：为所有 scene_label 在 user_scene_weight 中插入一行（weight=0），
        保证该用户参与场景排序时有一致的权重来源。
        """
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT IGNORE INTO user_scene_weight (user_id, label_id, weight)
                    SELECT %s, label_id, 0.00 FROM scene_label
                    """,
                    (user_id,),
                )
            conn.commit()
        finally:
            conn.close()

    def get_label_id_by_scenes(
        self,
        first_scene: str,
        second_scene: str,
        third_scene: Optional[str] = None,
    ) -> Optional[int]:
        """
        根据一级/二级/三级场景名解析 label_id。
        若 third_scene 未传，则返回该 (first, second) 下任意一个三级场景的 label_id（取第一个）。
        """
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                if third_scene:
                    cur.execute(
                        "SELECT label_id FROM scene_label WHERE first_scene = %s AND second_scene = %s AND third_scene = %s LIMIT 1",
                        (first_scene.strip(), second_scene.strip(), third_scene.strip()),
                    )
                else:
                    cur.execute(
                        "SELECT label_id FROM scene_label WHERE first_scene = %s AND second_scene = %s ORDER BY label_id LIMIT 1",
                        (first_scene.strip(), second_scene.strip()),
                    )
                row = cur.fetchone()
                return int(row["label_id"]) if row else None
        finally:
            conn.close()

    def find_chunk_by_text(self, text: str, category: Optional[int] = None) -> Optional[Dict]:
        """
        按语块/句型原文查找 chunk_core 记录（忽略大小写）。
        若传入 category，则同时过滤类型。返回包含 chunk_id, chunk, category, difficulty 等的字典。
        """
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                if category is not None:
                    cur.execute(
                        "SELECT chunk_id, chunk, difficulty, category, weight FROM chunk_core WHERE LOWER(TRIM(chunk)) = LOWER(TRIM(%s)) AND category = %s LIMIT 1",
                        (text, category),
                    )
                else:
                    cur.execute(
                        "SELECT chunk_id, chunk, difficulty, category, weight FROM chunk_core WHERE LOWER(TRIM(chunk)) = LOWER(TRIM(%s)) LIMIT 1",
                        (text,),
                    )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def add_chunk(
        self,
        chunk_text: str,
        category: int,
        difficulty: int,
        label_id: int,
        weight: float = 0.0,
    ) -> Dict:
        """
        新增语块/句型到 chunk_core 并绑定到指定场景。
        category: 1=语块, 2=句型；difficulty: 1/2/3。
        若 chunk 已存在（同文同类型），则返回已有记录并确保 mapping 存在；否则插入并返回新记录。
        """
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                chunk_text = chunk_text.strip()
                cur.execute(
                    "SELECT chunk_id FROM chunk_core WHERE LOWER(TRIM(chunk)) = LOWER(%s) AND category = %s LIMIT 1",
                    (chunk_text, category),
                )
                row = cur.fetchone()
                if row:
                    cid = int(row["chunk_id"])
                    cur.execute(
                        "INSERT IGNORE INTO chunk_scene_mapping (chunk_id, label_id) VALUES (%s, %s)",
                        (cid, label_id),
                    )
                    conn.commit()
                    cur.execute("SELECT chunk_id, chunk, difficulty, category, weight FROM chunk_core WHERE chunk_id = %s", (cid,))
                    return dict(cur.fetchone())
                cur.execute(
                    """
                    INSERT INTO chunk_core (chunk, difficulty, category, learn_count, correct_count, last_correct, weight)
                    VALUES (%s, %s, %s, 0, 0, 1, %s)
                    """,
                    (chunk_text, difficulty, category, weight),
                )
                conn.commit()
                cid = cur.lastrowid
                cur.execute("INSERT INTO chunk_scene_mapping (chunk_id, label_id) VALUES (%s, %s)", (cid, label_id))
                conn.commit()
                cur.execute("SELECT chunk_id, chunk, difficulty, category, weight FROM chunk_core WHERE chunk_id = %s", (cid,))
                return dict(cur.fetchone())
        finally:
            conn.close()

    def get_user_chunk_progress(self, user_id: str) -> List[Dict]:
        """获取某用户所有语块学习进度（用于统计或 UI）。"""
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT p.chunk_id, p.learn_count, p.correct_count, p.last_correct, p.last_learned_at,
                           c.chunk, c.category, c.difficulty
                    FROM user_chunk_progress p
                    JOIN chunk_core c ON c.chunk_id = p.chunk_id
                    WHERE p.user_id = %s
                    ORDER BY p.last_learned_at DESC
                    """,
                    (user_id,),
                )
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
