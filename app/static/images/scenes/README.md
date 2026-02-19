# 场景本地图片规范

本目录用于存放**大场景、小场景、NPC**的展示图，风格与读取规则统一。

## 一、三类图片与命名规则

| 类型 | 文件名规则 | 缺省占位图 | 说明 |
|------|------------|------------|------|
| **小场景** | `{small_scene_id}.jpg` 等 | `default.svg` | 与 dialogues 中 small_scene_id 一致，如 `bank.jpg`、`home.png` |
| **大场景** | `big_{big_scene_id}.jpg` 等 | `default_big.svg` | 如 `big_daily.jpg`、`big_food.png` |
| **NPC** | `npc_{character_id}.jpg` 等 | `npc_avatar.svg` | 未单独配图时统一使用简单人像图标；可选为某角色放 `npc_home_family.jpg` 等 |

- **格式**（按优先级）：`.jpg`、`.png`、`.jpeg`、`.webp`、`.svg`。
- **读取**：后端按类型在 `app/static/images/scenes/` 下查找对应文件名，无则返回缺省图 URL；前端直接使用接口返回的 `image` 字段。

## 二、小场景图

- 若某小场景未放置对应文件，将使用 **default.svg** 作为占位图。
- **每次启动主站时**，脚本会为所有有沉浸式对话的小场景检查本目录：若某场景没有任何图片，会自动将 `default.svg` 复制为 `{small_scene_id}.svg`。
- 可随时用真实图替换：放入同名文件（如 `bank.jpg`），系统会优先使用该图。

## 三、大场景图

- 大场景列表与进入小场景前的「大场景卡片」使用 **big_{id}** 图，缺省为 **default_big.svg**。
- 启动时脚本会为每个大场景生成 `big_{id}.svg` 占位图（从 default_big.svg 复制），可用 `big_daily.jpg` 等替换。

## 四、NPC 图

- 场景详情中的 NPC 卡片、以及与 NPC 对话时的练习界面会显示 **NPC 头像**。未为某角色单独配图时，统一使用 **npc_avatar.svg**（简单人像图标）。
- 若需为某角色单独配图，可放置 `npc_{character_id}.jpg` 等（如 `npc_cafe_waiter.png`），系统会优先使用。

## 五、新增场景 / NPC 时

1. 在 `data/dialogues.json` 中增加对话（含 `big_scene`、`small_scene`、`usage: "immersive"` 等）。
2. **重启主站**（或手动运行 `python scripts/build_scene_npc_index.py`）：索引会更新，并自动生成对应占位图。
3. （可选）在本目录下放入真实图片，文件名按上表规则。

## 六、当前小场景与大场景图（已覆盖）

**大场景**：`big_daily.png`、`big_food.png`、`big_transport.png`、`big_shopping.png`、`big_work.png`、`big_social.png`

**小场景**：`home`、`community`、`park`、`hospital`、`bank`、`cafe`、`restaurant`、`fast_food`、`snack_shop`、`airport`、`train_station`、`bus_metro`、`taxi`、`hotel`、`supermarket`、`mall`、`barber`、`cinema`、`office`、`interview`、`meeting`、`phone`、`party`、`chat`、`hobby`、`praise`（均为 `.png` 或 `.jpg` 等，与 `dialogues.json` 中 `small_scene` 一致）。

**获取方式任选其一：** 免费图库（Unsplash、Pexels）搜索对应英文关键词；或使用 `scripts/copy_scene_images.py`（见项目文档）；或自行 AI 生图/拍照，文件名与上表一致即可。
