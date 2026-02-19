# 场景索引与本地图片

## 一、场景索引（scene_npc_index.json）

为加快沉浸式场景列表与详情的加载，后端可优先使用**预生成的索引文件**，不再在每次请求时遍历整份 `dialogues.json`。

### 自动刷新（推荐）

**每次启动主站（FastAPI）时，会自动执行索引脚本**，完成两件事：

1. 根据当前 `data/dialogues.json` 生成/覆盖 `data/scene_npc_index.json`。
2. 对每个有沉浸式对话的小场景，若 `app/static/images/scenes/` 下尚无该场景的图片（如 `bank.jpg`、`cafe.svg`），则自动将 `default.svg` 复制为 `{small_scene_id}.svg`，作为占位图。

因此**无需人工执行命令**；改完 `dialogues.json` 后，只要重启一次主站，索引与占位图都会更新。

### 手动执行（可选）

若希望在未重启的情况下刷新索引与占位图，可在项目根目录执行：

```bash
python scripts/build_scene_npc_index.py
```

或 `npm run build:scene-index`。执行后需调用 `reload_dialogues()` 或重启主站，新索引才会被后端加载。

### 行为说明

- **有索引时**：大场景列表、小场景列表、场景详情均从索引读取，响应更快。
- **无索引时**：后端自动回退为现场从 `dialogues.json` 推导，功能正常，仅首屏略慢。

---

## 二、场景本地图片（大场景 / 小场景 / NPC）

场景与 NPC 的图片均来自 **`app/static/images/scenes/`**，风格与读取规则一致。

### 规范

| 类型 | 文件名规则 | 缺省 |
|------|------------|------|
| 小场景 | `{small_scene_id}.jpg` 等，如 `bank.jpg`、`cafe.png` | **default.svg** |
| 大场景 | `big_{big_scene_id}.jpg` 等，如 `big_daily.jpg` | **default_big.svg** |
| NPC | `npc_{character_id}.jpg` 等，如 `npc_cafe_waiter.png` | **default_npc.svg** |

- 格式：支持 `.jpg`、`.png`、`.jpeg`、`.webp`、`.svg`（按优先级使用先找到的）。
- 前端：大场景列表、小场景列表、场景详情背景、NPC 卡片及**与 NPC 对话时的练习界面**均使用接口返回的 `image` 字段（本地 URL），直接加载即可。

### 新增场景 / NPC 时

1. 在 `data/dialogues.json` 中增加对话（含 `usage: "immersive"` 等）。
2. **重启主站**（或手动运行 `python scripts/build_scene_npc_index.py`）：索引会更新，并为缺失的大场景、小场景、NPC 自动生成对应占位图（`big_*.svg`、`{small_scene_id}.svg`、`npc_*.svg`）。
3. （可选）用真实图片替换占位图：按上表文件名放入 `app/static/images/scenes/` 即可。

更细的说明见 **`app/static/images/scenes/README.md`**。

---

## 三、数据库 / 场景更新时的必做项

每次更新 **data/dialogues.json** 或大/小场景、NPC 结构时，除刷新索引与占位图外，**必须**同步更新内置的「推荐主题」判断逻辑，否则学习推荐与数据库会不一致：

- **文件**：`app/scene_npc_db.py`
- **函数**：`infer_theme_scene_from_conversation(text)`（从对话摘要推断 big_scene_id, small_scene_id）
- **做法**：根据新增或调整的大场景、小场景，在该函数内补充或修改关键词与 `(big_scene_id, small_scene_id)` 的映射（如新增出行、购物等场景时增加对应关键词分支）。

推荐主题仅用该内置规则，不调用 LLM。

---

## 四、排查「换图后仍显示旧图」

可能原因与对应处理：

| 原因 | 处理 |
|------|------|
| 后端进程内缓存了旧的图片 URL（.svg） | 已做：启动时清空 `_SCENE_IMAGE_URL_CACHE`；每次打开场景弹窗会清空前端场景列表缓存，重新拉接口。 |
| 浏览器强缓存同一 URL 的图片 | 已做：图片 URL 带 `?t=文件修改时间`，换文件后 URL 变化；静态资源使用 `StaticFilesNo304`，不返回 304，避免误用旧缓存。 |
| 后端读图目录与真实放图目录不一致 | 已做：场景图目录与 data 同项目根（`_project_dir()/app/static/images/scenes`）；静态挂载用项目根绝对路径。 |

### 调试接口

在浏览器或 Postman 请求：

```http
GET /api/scene-npc/debug-scene-images
```

返回示例：

```json
{
  "images_dir": "C:\\...\\voice-chat-ai\\app\\static\\images\\scenes",
  "dir_exists": true,
  "sample_files": { "home": { ".png": true, ".svg": true }, ... },
  "sample_urls": { "home": "/app/static/images/scenes/home.png?t=1739...", ... }
}
```

- 若 `sample_files.home[".png"]` 为 `false`，说明**运行中的进程**在该路径下没找到 `home.png`，需要把 PNG 放到 `images_dir` 所示目录，并**重启后端**。
- 若为 `true` 但前端仍显示旧图：**强刷页面（Ctrl+F5）** 后再次打开「进入场景体验」，确认是否已显示新图。

### 路径建议（避免中文）

建议将**项目根目录**放在仅含英文的路径下，例如：

- 推荐：`C:\Users\YourName\Desktop\projects\EnglishApp\voice-chat-ai`
- 不推荐：`C:\Users\YourName\Desktop\编程项目\EnglishApp\voice-chat-ai`

这样可避免终端、脚本在复制/解析路径时出现编码问题。若当前项目路径含中文，可将整个 `voice-chat-ai` 文件夹移动到英文路径下再打开。
