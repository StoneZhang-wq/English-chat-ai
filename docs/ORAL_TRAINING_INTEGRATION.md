# 口语训练数据库与业务集成规范

本文档约定：**仅使用** `data/oral_training_db.json` 时，场景选择、卡片生成、练习与复习的业务规则。实现相关功能时必须遵循本规范。

---

## 一、用户仅选「场景 + 难度」

- 前端只让用户选择：**scene**（如 Daily Life、Eating Out、Shopping）、**difficulty**（Simple / Intermediate / Difficult）。
- **难度**仅来自 oral_training_db 的 `difficulty` 枚举；若日后 DB 增加新难度，选择项随之增加。
- **Unit 与 A/B/C 批次**由系统根据用户学习记录自动判断，用户不选。

---

## 二、同一 Unit 下 A/B/C 与「掌握」规则

- 同一 Unit 下 A、B、C 三批次的**核心知识点相同**（core_sentences、core_chunks 一致）。
- **掌握定义（用户自评 + 默认掌握）**：
  - 用户完成某批次（如 A）并生成复习笔记后，**由用户自评**：「掌握了」或「还没掌握」。
  - **用户选「掌握了」**：该 Unit 视为已掌握，**不再推送该 Unit 的 B/C**；下次选到同一 Unit 时不再出现后续批次。
  - **用户选「还没掌握」**：下次选到同一 Unit 时推送**下一批次**（A 后推 B，B 后推 C）。
  - **三个批次（A、B、C）都已被推荐/完成过**：即使用户未点「掌握了」，也**默认视为该 Unit 已掌握**（不再推新批次）。
- 实现要点：
  - 每个 (scene, unit) 记录：各批次 A/B/C 是否「完成会话」`completed`，以及可选 **`_mastered`**（用户曾自评「掌握了」）。
  - 若 `_mastered` 为 true → 该 unit 视为已掌握，不再推 B/C。
  - 否则按 A → B → C 顺序推送第一个未 completed 的批次；若 A/B/C 均已 completed，则视为默认掌握。

---

## 三、场景列表：recommended + frequent + new

生成英语卡片前展示的「可选场景」由三类组成：

| 类型 | 含义 | 来源 |
|------|------|------|
| **recommended** | 根据中文对话推荐 | 摘要关键词 → scene 映射表，最多 1 个 |
| **frequent** | 用户常选 | 按该用户「场景选择次数」排序，取前若干（如 2～3 个），排除已在 recommended 的 |
| **new** | 用户从未学过 | 在该用户下，该 scene 下没有任何 unit 的练习记录，取 1～2 个 |

合并去重后返回；每条含 `scene`、`label`（recommended / frequent / new）、可选 `choice_count`（frequent 时展示「已选 N 次」）。

---

## 四、摘要推荐场景：关键词 → scene 表

中文对话结束后，用摘要文本匹配下表，得到「推荐场景」`suggested_scene`（用于场景列表的 recommended 项）。

| scene | 关键词（任一词命中即可） |
|-------|---------------------------|
| Daily Life | 日常 工作 上班 作息 时间 周末 计划 习惯 感觉 压力 生活 |
| Eating Out | 吃 餐厅 点餐 外卖 做饭 饭 菜 咖啡 菜单 |
| Shopping | 买 购物 逛街 商店 价格 衣服 鞋 包 |

- 匹配方式：摘要中是否包含某关键词（子串或分词后匹配）；命中多场景时取其一（如优先第一个命中或计数最多）。
- 若无命中，`suggested_scene` 为 null，场景列表仅含 frequent + new。

---

## 五、用户数据（与旧库无关）

在 `memory/accounts/{account_name}/` 下仅维护一个文件 **unit_practice.json**，内合两类数据：

1. **scene_choices**（保留键）  
   - 结构：`"scene_choices": { "Daily Life": 5, "Eating Out": 2, "Shopping": 0 }`  
   - 含义：用户「在生成英语卡片前」选择该场景的次数。  
   - 更新：用户选定场景并确认时（如调用 select-scene）该 scene 计数 +1。

2. **各场景的 unit 完成情况**（顶层键为场景名）  
   - 结构：按 scene → unit → batch 记录是否完成会话；unit 下可有保留键 **`_mastered`** 表示用户自评「掌握了」。  
   - 示例：`"Daily Life": { "U1-Daily Routine": { "A": { "completed": true }, "B": {}, "C": {}, "_mastered": true }, ... }, ... }`  
   - 用于判断：该 unit 是否已掌握；若未掌握，下次应推 A / B / C 中的哪一个。

整体示例：`{ "scene_choices": { "Daily Life": 1 }, "Daily Life": { "U1-Daily Routine": { "A": { "completed": true }, "_mastered": true } }, ... }`

---

## 六、复习资料组成

复习资料必须包含三者：

1. **（1）Review 行**：同 scene + unit、batch=Review 的那条记录的对话内容（可带 hint），作为「复习用对话」。
2. **（2）核心句型与语块**：当前练习卡片对应记录的 `core_sentences`、`core_chunks`。
3. **（3）AI 纠错与建议**：根据本次练习的 user_inputs 与参考台词，由 AI 生成 corrections / suggestions。

---

## 七、与旧数据源的关系

- 本集成方案**仅使用** `data/oral_training_db.json`。
- 不再依赖 `scenes.json`、`chunks.json`、`chunk_scene_mapping.json` 及基于它们的推荐/生成逻辑。
- 场景展示使用英文（与 DB 中 `scene` 一致）。
