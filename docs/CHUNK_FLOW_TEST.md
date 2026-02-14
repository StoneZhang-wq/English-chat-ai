# 新用户语块流程测试报告

## 测试环境与方式

- **环境**：默认使用文件后端（data/*.json），无需 MySQL。若设置 CHUNK_BACKEND=mysql 则需 MySQL 已建表并导入数据。
- **方式**：代码走读 + 逻辑推演 + 前端/后端接口与数据流核对。

---

## 一、可跑通的前提

| 条件 | 说明 |
|------|------|
| MySQL 已安装并运行 | 语块库依赖 MySQL |
| 环境变量已配置 | `CHUNK_DB_HOST` / `CHUNK_DB_PORT` / `CHUNK_DB_USER` / `CHUNK_DB_PASSWORD` / `CHUNK_DB_NAME` |
| `pip install pymysql` | 已安装 |
| 存在 `data/scenes.json`、`data/chunks.json`、`data/chunk_scene_mapping.json` | 文件后端默认数据（项目已自带） |

在上述前提下，**登录 → 开始英语学习 → 选场景 → 选长度/难度 → 生成卡片** 在逻辑上可以跑通；未满足时会出现下面「不可跑通」的情况。

---

## 二、不可跑通或易错点（需你确认后再改）

### 1. 未配置 MySQL / 未建表 / 未种子数据

- **现象**：
  - 文件后端：若 `data/` 下 JSON 缺失或为空，`get_available_scenes()` 返回空列表，生成卡片时提示无可用语块。
  - MySQL 后端（CHUNK_BACKEND=mysql）：未配置或未启动 MySQL 时连接失败；未建表/未导入数据时同上。
- **结论**：流程依赖「建表 + 种子数据」；文档已说明，无需改代码，只需按文档操作。

---

### 2. 前端只传「一级+二级」、不传 `label_id`，且同一 (一级,二级) 下存在多个三级场景时会选错场景 —— **已修复**

- **原现象**：后端按三级场景返回多行，前端只显示「一级 - 二级」且不传 `label_id`，多三级时会选错场景。
- **已实现**：前端场景按钮展示「一级 - 二级 - 三级」（有 `scene_tertiary` 则显示）；选中后优先传 `label_id` 给 `select-scene` 和 `english/generate`，无则退化为 scene_primary + scene_secondary；选中高亮按 `label_id` 匹配。

---

### 3. 可选：无可用场景时的前端提示 —— **已实现**

- **已实现**：当「全部场景」为空时，弹窗中显示「暂无可用场景，请先配置语块库（确认 data/ 下 scenes.json、chunks.json 已就绪）」。

---

## 三、当前流程串联检查（在「建表+种子+MySQL+登录」均就绪时）

| 步骤 | 接口/行为 | 结果 |
|------|-----------|------|
| 1. 登录 | POST 登录，后端 `init_user_progress(account_name)` | 为该用户在所有 scene_label 下插入 user_scene_weight(weight=0)；MySQL 失败时仅打 Warning，登录仍成功 |
| 2. 开始英语学习 | POST `/api/conversation/end` | 返回 suggested_scenes、available_scenes（来自 chunk_db）；失败时 available_scenes=[] |
| 3. 选场景 | 前端用 available_scenes 展示「一级 - 二级 - 三级」按钮；选后 POST `/api/knowledge/select-scene`（优先传 label_id） | 后端按 label_id 或 scene_primary+scene_secondary 更新 user_scene_weight |
| 4. 选长度/难度 | 前端弹窗 | 正常 |
| 5. 生成卡片 | POST `/api/english/generate`（优先传 scene_label_id，兼容 scene_primary + scene_secondary） | 后端按 scene_label_id 或场景名得到 label_id，get_recommended_chunks(..., selected_label_id)；有种子数据时可返回语块并生成对话 |
| 6. 保存练习 | POST `/api/practice/save-memory`（或等价） | 从 review_notes 提词汇/语法，find_chunk_by_text / add_knowledge_to_master，update_chunk_progress，update_scene_preference；逻辑正确 |

---

## 四、结论与已完成的修改

- **在「MySQL + 建表 + 种子数据 + pymysql」都就绪的前提下**，新用户流程可以跑通；同一 (一级,二级) 下多三级场景时也能正确按 `label_id` 选场景。
- **已完成的修改**：
  1. 前端选场景时展示「一级 - 二级 - 三级」，并优先传 `label_id` 给 select-scene 和 english/generate。
  2. 无可用场景时在弹窗中显示「请先配置语块库（确认 data/ 下 scenes.json、chunks.json 已就绪）」。
