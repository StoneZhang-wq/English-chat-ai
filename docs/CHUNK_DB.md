# 语块/句型数据（场景 + 语块 + 卡片推荐）

**说明**：支持两种后端，**默认无需数据库**。

| 后端 | 说明 | 何时使用 |
|------|------|----------|
| **文件（默认）** | 使用 `data/scenes.json`、`data/chunks.json`、`data/chunk_scene_mapping.json`；用户进度在 `memory/accounts/<用户>/` 下。 | 不安装 MySQL 即可用，开箱即用。 |
| **MySQL** | 使用 chunk_core、scene_label、chunk_scene_mapping 等表。 | 设置环境变量 `CHUNK_BACKEND=mysql` 且已建表、导入种子数据后使用。 |

---

## 一、首次使用（文件后端，默认）

**无需安装 MySQL**。项目已自带 `data/` 下初始场景与语块，直接启动应用即可：

1. 启动应用，用户登录后进入语音对话。
2. 结束对话后选择一级场景下的 3 个二级选项之一，即可生成英语卡片。

验证流程（可选）：`python test_chunk_flow.py`（默认走文件后端）。

若要**自行增改场景/语块**：编辑 `data/scenes.json`、`data/chunks.json`、`data/chunk_scene_mapping.json` 即可。

---

## 二、使用 MySQL 时（可选）

仅当设置 **CHUNK_BACKEND=mysql** 时才会连接 MySQL。需自行在 MySQL 中按 `docs/sql/chunk_schema.sql` 建库建表，并导入场景与语块数据；同时配置环境变量 `CHUNK_DB_*`。

---

## 三、用户专属数据何时生成（文件后端）

两个用户专属表都不是「建表时」就按用户预先建好，而是**按需生成**：

| 表 | 何时生成 / 写入 | 说明 |
|----|-----------------|------|
| **user_scene_weight** | ① 用户**首次登录**时：`init_user_progress(user_id)` 为该用户在**当前所有** `scene_label` 下插入一行 `weight=0`。<br>② **之后新增场景**：管理员或种子脚本新增 `scene_label` 后，老用户在**首次请求推荐**（生成卡片）时会执行 `init_user_scene_weights(user_id)`，补全新场景的 `weight=0` 行（懒同步）。 | 保证「每个用户 × 每个场景」都有一条权重，推荐排序一致；新用户登录即全量初始化，老用户在新场景上按需补全。 |
| **user_chunk_progress** | 用户**首次练习到某语块**时：保存练习时调用 `update_chunk_progress(user_id, chunk_id, is_correct)`，执行 `INSERT ... ON DUPLICATE KEY UPDATE`，没有则插入一条（学习次数、正确次数、last_correct）。 | 不做预创建；只在该用户真正练过某条语块时才有一条记录。 |

因此：

- **新用户**：登录 → 只初始化 `user_scene_weight`；`user_chunk_progress` 在第一次保存练习后才有数据。
- **老用户**：新增了场景（在 data/scenes.json）后，第一次点「生成英语卡片」时会自动补全该用户 `scene_weights.json` 中新场景的权重，无需重新登录。

---

## 四、表结构概览（MySQL 时） / 文件结构（文件后端）

| 表名 | 说明 |
|------|------|
| **chunk_core** | 语块/句型核心表。语块(category=1)含词组/单词/俚语，句型(category=2)含语法/句子。 |
| **scene_label** | 场景标签表。一级/二级/三级场景 + 权重。 |
| **chunk_scene_mapping** | 语块-场景多对多。(chunk_id, label_id) 联合主键。 |
| **user_scene_weight** | （多用户）用户在某场景下的兴趣权重。 |
| **user_chunk_progress** | （多用户）用户语块学习进度：学习次数、正确次数、上次是否正确。 |

- 文件后端：场景即 `data/scenes.json`，语块即 `data/chunks.json`，关联即 `data/chunk_scene_mapping.json`；用户权重与进度在 `memory/accounts/<用户>/scene_weights.json`、`chunk_progress.json`。  
- MySQL 时建表语句见：`docs/sql/chunk_schema.sql`。

## 五、枚举约定

- **chunk_core.difficulty**：1=最低，2=中等，3=最高。
- **chunk_core.category**：1=语块，2=句型。
- **last_correct**：0=上次错误，1=上次正确。

## 六、卡片生成优先级（严格遵循）

1. **场景层级**
   - 第一步：优先生成「权重最高的三级场景」对应的所有语块/句型（或用户手动选择的该三级场景）。
   - 第二步：该三级场景内容用完后，生成「同一二级场景下、其他未学习的三级场景」对应内容，按场景权重排序。
   - 第三步：该二级下所有三级用完后，生成「同一一级场景下、其他未学习的二级（及下属三级）」对应内容，按场景权重排序。

2. **附加**
   - 支持用户手动切换至任意场景；切换后以该场景为起点，再按「三级→二级→一级」层级扩展。
   - 同一场景下语块/句型按 **chunk_core.weight** 二次排序；可兼顾 **difficulty**（如新手优先难度 1）、**last_correct**（上次错误优先复现）。

## 七、环境变量（MySQL）

| 变量 | 说明 | 默认 |
|------|------|------|
| CHUNK_DB_HOST | 主机 | 127.0.0.1 |
| CHUNK_DB_PORT | 端口 | 3306 |
| CHUNK_DB_USER | 用户 | root |
| CHUNK_DB_PASSWORD | 密码 | （空） |
| CHUNK_DB_NAME | 数据库名 | english_chunk |

依赖：`pip install pymysql`。

## 八、代码使用（app/chunk_db.py）

```python
from app.chunk_db import ChunkDatabase, DIFFICULTY_MAX, CATEGORY_CHUNK, CATEGORY_PATTERN

db = ChunkDatabase()

# 所有可用场景（含 label_id、first/second/third_scene）
scenes = db.get_available_scenes()

# 推荐语块/句型（按场景层级 + 同场景内 weight/difficulty/last_correct）
chunks = db.get_recommended_chunks(
    user_id="user_001",
    user_difficulty_max=2,           # 只推荐难度 1、2
    selected_label_id=5,             # 用户手动选的场景；None 则按权重最高三级
    limit=20,
    prefer_wrong_first=True,
)

# 用户选择某场景时：增加该场景权重
db.increment_scene_choice("user_001", label_id=5)

# 练习后更新学习进度
db.update_chunk_progress("user_001", chunk_id=10, is_correct=True)
```

## 九、与现有接口的衔接（已实现）

- **get_available_scenes**：由 `KnowledgeDatabase().get_available_scenes()` 委托到 `ChunkDatabase().get_available_scenes()`，返回含 `label_id`、`first_scene`/`second_scene`/`third_scene` 及兼容字段 `scene_primary`/`scene_secondary`/`scene_tertiary`。
- **select-scene**：支持传 `label_id`（优先）或 `scene_primary`+`scene_secondary`；传 `label_id` 时调用 `increment_scene_choice_by_label`，否则按场景名解析 `label_id` 后调用 `increment_scene_choice`，更新用户专属表 `user_scene_weight`。
- **english/generate**：接收 `scene_primary`、`scene_secondary` 及可选 `scene_label_id`；推荐内容来自 `get_recommended_chunks(..., selected_label_id=scene_label_id)`，prompt 使用「必须使用的语块」「必须使用的句型」。
- **save_practice_memory**：从复习笔记提取重点词汇/语法后，用 `find_chunk_by_text` 在 `chunk_core` 中匹配；有则更新 `user_chunk_progress`，无则 `add_knowledge_to_master`（写入 `chunk_core` + `chunk_scene_mapping`）再更新进度；最后 `update_scene_preference` 更新 `user_scene_weight`。
