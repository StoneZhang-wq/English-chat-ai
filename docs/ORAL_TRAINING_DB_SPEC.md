# 口语训练数据库规范（ORAL_TRAINING_DB_SPEC v1.1）

> 目标：在不破坏原有工程结构与业务逻辑的前提下，提升**可生成性、自然口语度与长期维护成本可控性**。

本文档为口语训练数据库的权威规范，用于生成与完善 `data/oral_training_db.json`。程序读取、人工扩展或 AI 完善数据库时，均应严格遵循本规范。

---

## 一、程序用数据格式

- **主数据文件**：`data/oral_training_db.json`
- **每条记录字段**（英文键名）：
  - `scene`：场景
  - `difficulty`：难度（Simple / Intermediate / Difficult）
  - `unit`：单元（如 U1-Daily Routine）
  - `batch`：批次（A / B / C / Review）
  - `dialogue_id`：对话ID（如 DL-S-U1-A）
  - `content`：对话内容，**必须是数组**，每项为 `{"role":"A"|"B", "content":"...", "hint":"..."}`
  - `core_sentences`：核心句型，用 `/` 分隔
  - `core_chunks`：核心语块，用 `/` 分隔
- 表格导出（可选）：`data/oral_training_db.md`，列名：场景 | 难度 | 单元 | 批次 | 对话ID | 完整内容(JSON) | 核心句型 | 核心语块；单元格内禁止换行，JSON 写在一行。

---

## 二、数据库结构模型

- **场景**：如 Daily Life、Eating Out、Shopping（可扩展，需在「对话ID规则」中约定缩写）。**原有场景**每难度 5 个 Unit；**新增场景**每难度 3 个 Unit。
- **难度**：仅允许 **Simple**、**Intermediate**、**Difficult** 三种。
- **Unit 数量**：**原有场景**（Daily Life、Eating Out、Shopping）每个难度下 **5 个 Unit**（U1–U5）；**新增场景**每个难度下 **3 个 Unit**（U1、U2、U3）。每个 Unit 有主题。
- 每个 Unit 包含批次：**A**、**B**、**C**、**Review**。

---

## 三、对话 content（JSON）格式、长度与逻辑性

- 必须为**数组**，每句为对象，含 `role`、`content`、`hint`。
- **每条记录的 content 长度（按难度）**：
  - **Simple**：4 轮对话，共 **8 条**（4 问 4 答）。
  - **Intermediate**：8 轮对话，共 **16 条**（8 问 8 答）。
  - **Difficult**：12 轮对话，共 **24 条**（12 问 12 答）。
  - **Review** 批次：与同难度一致（8 / 16 / 24 条）；不再提供「精简 30%」选项（v1.1）。
- **对话逻辑性**：整段对话须为完整、连贯的一段对话，有明确话题或交际目标；轮与轮之间可有追问、补充、转折，但不跳题；禁止同一问一答简单重复多遍或无上下文拼凑。生成时先按轮数设计多轮内容，再写每句 content 和 hint。
- **Hint 生成**：每句 hint 在该句 content 确定后写；以结构提示为主，可带 1～2 个关键词；同一 Unit 下 A/B/C 同一轮次的 hint 结构一致；hint 中的关键表达须出现在该条的 `core_sentences` 或 `core_chunks` 中。

---

## 四、难度分层规则（v1.2）

**目标**：像真实聊天，而非句型操练；结构覆盖与自然度并重。

| 难度 | 要求 |
|------|------|
| **Simple** | **目标**：像小白真实聊天，而不是「英语句型操练」。以简单句为主；because ≤1 次（仅限 because + 简短原因）；不允许 if 条件句、宾语从句；句长 ≤12 词（允许 +2 容错）；只使用基础时态。**允许 1～2 句「弱信息句」**（纯回应），如：Sure. / Okay. / Sounds good. / Really? |
| **Intermediate** | **目标**：像「能聊天的普通人」，不是「语法展示会」。**同一 Unit 的 A/B/C 整体覆盖 2 种结构**：because / if / I think (that)（不要求单条必须覆盖 2 种）；单条至少 1 个从句；允许现在完成时；句长 ≤18 词（允许 +2 容错）。**允许 2～3 句「功能性废话」**，如：I see. / That makes sense. / Yeah, maybe. |
| **Difficult** | **目标**：像真实成年人讨论问题，而不是「复杂句型拼盘」。**同一 Unit 内整体覆盖（A/B/C 合计）**：although / even though；if + would；至少 1 个抽象表达；**单条对话最多强制 2 类结构点**；句长 ≤25 词（允许 +2 容错）。**允许自然插话 1～2 次**，如：To be honest, / You know, / The thing is, |

---

## 五、Unit 差异规则

不同 Unit 必须：话题功能不同、核心句型不同、核心语块不同、交际目标不同；**不能**只是名词替换。不同 Unit 的整段对话应有不同的话题与交际目标，归纳出的核心句型与核心语块也须不同。

---

## 六、批次规则（A / B / C）

同一 Unit 下 A、B、C：语法结构、核心句型、对话轮数、hint 结构完全一致，核心知识点相同，仅替换细节词汇。业务上：用户完成某批次后自评「掌握了」即 unit 掌握（不再推 B/C）；选「还没掌握」则下次推下一批次（A→B→C）；A/B/C 三批次都推荐完后默认 unit 掌握。详见 `ORAL_TRAINING_INTEGRATION.md`。

---

## 七、Review 生成逻辑（v1.1 收紧）

- **轮数（统一标准）**：Simple 4 轮（8 条）、Intermediate 8 轮（16 条）、Difficult 12 轮（24 条）。**不再提供「精简 30%」选项**，Review 统一与同难度 A/B/C 轮数一致。
- **来源**：Review 为同 Unit A/B/C 的「关键轮次压缩重组版」；不引入新句型/语块；hint 与 core_sentences/core_chunks 与 A/B/C 一致或子集。
- **共用**：同一 Unit 下 A/B/C 共用一套 Review（一条记录）。

---

## 八、核心句型与核心语块（生成顺序与归纳）

- **生成顺序**：在整条记录的 content 全部写完后，再从该条对话中归纳；禁止未写满整段 content 就定死句型/语块。
- **核心句型**：从对话提炼语法框架/句型，覆盖本 Unit 语法重点及所有 hint 中的结构提示；同一 Unit 下 A/B/C 的 core_sentences 列表一致。用 `/` 分隔。
- **核心语块**：从对话提炼搭配、功能表达、场景词组（中高级可含抽象表达）；A/B/C 的 core_chunks 可因用词有少量差异，但功能/类型一致。检查：每个 hint 的关键表达在 core_sentences 或 core_chunks 中有对应。用 `/` 分隔。

---

## 九、对话ID规则

- **场景缩写**：Daily Life → DL；Eating Out → EO；Shopping → SH。**新增场景**：Travel → TR；Health → HL；Transport → TP；Work → WK；Education → ED；Weather → WH；Hobbies → HB；Family → FM；Technology → TC；Entertainment → ET。
- **难度缩写**：Simple → S；Intermediate → I；Difficult → D。
- **格式**：`场景缩写-难度缩写-Unit编号-批次`，例：DL-S-U1-A、EO-I-U1-Review、SH-D-U1-A。

**扩充场景与新增内容**：每次扩充（新增场景或新增 Unit）时，必须为新场景/新 Unit **全新编写**对话内容，不得复用或 fallback 到已有场景；之后每次扩充均须使用新写的对话，生成脚本中新增场景须显式定义并写入数据库。

---

## 十、完善数据库时的检查清单

1. `dialogue_id` 符合「场景-难度-Unit-批次」格式。
2. `content` 为数组，每句含 `role`、`content`、`hint`；hint 非完整句，且与核心句型/语块对应。
3. **content 条数**：Simple 8 条（4 轮）、Intermediate 16 条（8 轮）、Difficult 24 条（12 轮）；Review 与同难度一致（8/16/24）。
4. **对话逻辑性**：整段为完整连贯对话，有明确话题，轮与轮有上下文，无简单重复拼凑。
5. Simple/Intermediate/Difficult 句长与结构符合「难度分层规则」（v1.2）。
6. 同 Unit 下 A/B/C 结构一致；Review 与 A/B/C 同逻辑线、无新结构、共用一套。
7. 不同 Unit 之间话题、句型、语块有明确差异。
8. **口语自然度自检**：是否存在明显书面腔或中式直译；是否允许 1～2 处自然承接用语（Yeah / Right / Sure / That works. 等）；在不违反难度规则前提下，优先保证「像真实对话」。

---

## 十一、口语自然度原则（v1.1 补充）

- 优先使用真实口语中**高频表达**。
- 允许自然省略（如 Sure. / Sounds good. / That works.）。
- 允许 1～2 处自然重复或口头承接（Yeah / Right / I see.）。
- 在不违反难度规则前提下，**优先自然度而非模板对齐**。
