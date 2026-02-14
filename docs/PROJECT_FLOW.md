# Voice Chat AI 项目运行流程文档

> 最后更新时间：2026-01-31 | 如有与代码不符之处，以代码为准

---

## 一、项目概述

Voice Chat AI 是一个**英语学习语音对话应用**，支持多账户、多角色，集成豆包 / OpenAI 等 API。核心流程为：**中文沟通 → 生成英语卡片 → 练习模式 → 复习笔记**。

---

## 二、整体架构图

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   前端页面    │ ←→  │  FastAPI 服务  │ ←→  │  豆包/OpenAI  │
│ voice_chat   │ WebSocket/REST │   main.py    │   API 调用   │
└──────────────┘     └──────────────┘     └──────────────┘
       ↑                     ↑                     ↑
       │                     │                     │
  voice_chat.js         app_logic.py          doubao_client.py
  voice_chat.html       memory_system.py      app.py (LLM/TTS)
                        knowledge_db.py
```

---

## 三、板块划分与功能说明

### 板块 1：用户账户与会话入口

**功能：**
- 账号登录/创建、切换、退出
- 记忆系统初始化（按账号）
- 知识点数据库用户子表初始化

**实现：**
- `main.py`：`POST /api/account/login`、`GET /api/account/current`、`POST /api/account/logout`
- `shared.py`：`current_account`、`memory_system`，`get_memory_system(account_name)` 单例
- 数据目录：`memory/accounts/{用户名}/`（user_profile.json、diary.json、session_temp.json、learning_progress.csv、scene_preferences.csv）

**未来改进：** 密码/认证、数据导入导出、多设备同步

---

### 板块 2：中文沟通阶段

**功能：**
- 与 AI 用中文对话，了解兴趣、职业、学习目标、英文水平
- 首次沟通 vs 后续沟通的 prompt 区分
- 用户信息自动抽取并写入 user_profile

**实现：**
- `app_logic.py`：`process_text()` 根据 `learning_stage == "chinese_chat"` 使用中文 prompt
- `memory_system.py`：`save_to_session_temp()`、`extract_user_info()`、`update_user_profile()`
- 触发切换：用户说「开始学英语」→ `set_learning_stage("english_learning")`

**未来改进：** 更智能的信息抽取、兴趣标签、可配置触发词

---

### 板块 3：语音与文本输入

**功能：**
- 录音上传、转文字（ASR）
- 文本输入
- 支持豆包 ASR 或 OpenAI Whisper

**实现：**
- `main.py`：`POST /api/voice/upload`、`POST /api/text/send`
- `transcription.py`：`transcribe_audio()` 根据 `API_PROVIDER` 选择豆包或 OpenAI
- 前端 `voice_chat.js`：MediaRecorder 录制、上传、WebSocket 接收

**未来改进：** 支持更多 ASR 提供商、VAD、实时转写

---

### 板块 4：AI 对话生成与 TTS

**功能：**
- 根据角色 prompt、记忆上下文、学习阶段生成回复
- 情绪分析（mood）影响 prompt
- 文本转语音（TTS）并播放

**实现：**
- `app_logic.py`：`process_text()` 注入 `memory_system.get_memory_context()`
- `app.py`：`chatgpt_streamed_async()`（豆包/OpenAI）、`process_and_play()`（豆包/OpenAI/ElevenLabs/Kokoro/Spark-TTS）
- `doubao/doubao_client.py`：豆包 LLM、TTS、ASR 客户端

**未来改进：** 更多 LLM 支持、流式 TTS、多音色

---

### 板块 5：结束对话与摘要

**功能：**
- 生成当日会话摘要并写入日记
- 从摘要抽取用户信息
- 根据摘要推荐练习场景

**实现：**
- `main.py`：`POST /api/conversation/end`
- `memory_system.generate_diary_summary_from_temp()`、`add_diary_entry()`、`extract_user_info()`、`clear_session_temp()`、`get_suggested_scenes_from_summary()`

**未来改进：** 多轮摘要压缩、与知识图谱关联、敏感信息脱敏

---

### 板块 6：英语卡片生成

**功能：**
- 用户选择场景（scene_primary、scene_secondary）
- 用户选择难度（difficulty_level）、对话长度（short/medium/long/custom）
- 从 knowledge_base 获取该场景的知识点
- 结合用户水平、难度参数、历史练习生成英文对话
- 每句对话生成 TTS 音频

**API / 入口：**
- `POST /api/english/generate`（body: scene_primary, scene_secondary, difficulty_level, dialogue_length, custom_sentence_count）

**实现：**
- `main.py`：`POST /api/english/generate`
- `memory_system.generate_english_dialogue()`：调用 `KnowledgeDatabase.get_recommended_knowledge()`，根据 `ENGLISH_LEVELS` 生成难度说明，构建 prompt，生成 A/B 对话，逐句 TTS 保存到 `outputs/english_cards/`
- `knowledge_db.py`：`get_recommended_knowledge()` 考虑用户水平、掌握度、兴趣度、难度过滤

**未来改进：** 难度自适应、自定义知识点、对话缓存

---

### 板块 7：练习模式（跟读与校验）

**功能：**
- 用户按卡片逐句跟读，AI 说 A 句，用户说 B 句
- 校验用户表达与参考句意思一致性（check_meaning_consistency）
- 提示（phrases、pattern、words、grammar）由 `extract_hints()` 从参考句抽取
- 练习转写（不触发 AI 回复，节省 token）

**API / 入口：**
- `POST /api/practice/start`（解析卡片、初始化会话）
- `POST /api/practice/respond`（校验用户输入、返回下一句）
- `POST /api/practice/end`（返回完整会话数据）
- `POST /api/practice/hints`（按需获取提示）
- `POST /api/practice/transcribe`（练习模式专用转写）

**实现：**
- `main.py`：上述 API、`check_meaning_consistency()`、`extract_hints()` 调用 LLM
- 会话：`practice_sessions` 内存字典，`session_id` 贯穿

**未来改进：** 发音评估、流利度分析、知识点掌握度回写

---

### 板块 8：知识点数据库

**功能：**
- 总表 knowledge_base.csv，按场景（一级/二级）、类型、难度组织
- 用户子表：learning_progress.csv、scene_preferences.csv
- 掌握度、兴趣度、时间衰减计算

**API / 入口：**
- `POST /api/knowledge/select-scene`（记录用户场景选择）
- `GET /api/knowledge/available-scenes`（获取全部可选场景，供 UI 展示）
- `GET /api/knowledge/recommended`（获取推荐知识点，query: scene_secondary）

**实现：**
- `knowledge_db.py`：`KnowledgeDatabase` 的 `get_master_knowledge()`、`get_recommended_knowledge()`、`update_learning_progress()`、`update_scene_preference()`、`init_user_progress()`、`get_available_scenes()`

**未来改进：** 增量同步、遗忘曲线、在线编辑

---

### 板块 9：WebSocket 与实时通信

**功能：**
- 实时推送 AI 回复、用户消息、状态
- 支持切换角色、API provider、模型、语音

**实现：**
- `main.py`：`WebSocket /ws` 接收 start/stop/set_character/set_api_provider 等
- `app.send_message_to_clients()` 广播到所有连接客户端
- `shared.py`：`clients` 集合维护 WebSocket 连接

**未来改进：** 心跳重连、多房间、消息持久化

---

### 板块 10：难度与水平管理

**功能：**
- 用户英文水平设置（user_profile.english_level）
- 生成英语卡片时可覆盖难度（difficulty_level 参数）
- 知识库推荐时按用户水平过滤难度（可上浮一级）
- 支持等级：minimal、beginner、elementary、pre_intermediate、intermediate、upper_intermediate、advanced

**API / 入口：**
- `POST /api/user/update_english_level`（body: level, description）
- `POST /api/learning/start_english`（手动切换到英文学习阶段）

**实现：**
- `memory_system.py`：`ENGLISH_LEVELS` 配置、`get_difficulty_instructions()`、`update_english_level()`
- `knowledge_db.py`：`get_recommended_knowledge()` 中的难度过滤（allowed_levels）
- `shared.py`：`learning_stage`（chinese_chat / english_learning）

**未来改进：** 水平自测、分级推荐

---

### 板块 11：复习笔记生成

**功能：**
- 基于练习会话（user_inputs、dialogue_lines）生成个性化复习笔记
- 输出：词汇（key_words、new_words、difficult_words）、语法点、错误纠正、学习建议
- JSON 格式，供前端展示

**API / 入口：**
- `POST /api/practice/generate-review`（body: user_inputs, dialogue_topic）

**实现：**
- `main.py`：`generate_review_notes()` 调用 `chatgpt_streamed_async()` 生成 JSON
- 依赖：练习结束后由前端调用，需传入完整 user_inputs

**未来改进：** 与知识点 ID 关联、导出复习卡片

---

### 板块 12：练习进度（不再使用练习记录文件）

**功能：**
- 项目仅依赖 **unit_practice.json**（内合场景选择次数 + 场景/unit/批次完成状态）驱动推荐与复习
- `POST /api/practice/save-memory` 根据当次练习的 dialogue_id 更新 unit_practice（标记该批次已完成）
- 复习资料按需生成：纠错由 AI 生成，核心句型/语块与 Review 短对话从 oral_training_db 对应 Review 记录读取

**API / 入口：**
- `POST /api/practice/save-memory`（body: dialogue_id、review_notes 等，用于更新 unit_practice，不写入练习记录文件）

**实现：**
- `memory_system.py`：`save_practice_memory()` 只做 mark_batch_completed
- 进度存储：`memory/accounts/{用户名}/unit_practice.json`（内含 scene_choices 与各场景 unit 完成情况）

**未来改进：** 遗忘曲线复习提醒、按 unit_practice 生成复习列表

---

### 板块 13：场景选择与推荐

**功能：**
- 获取全部可选场景（来自 knowledge_base 的场景一级/二级）
- 用户选择场景后记录偏好（increment_scene_choice）
- 结束对话后根据摘要推荐场景（get_suggested_scenes_from_summary）
- 生成卡片前需用户选择 scene_primary、scene_secondary

**API / 入口：**
- `GET /api/knowledge/available-scenes`（场景列表）
- `POST /api/knowledge/select-scene`（记录选择）
- `POST /api/conversation/end` 返回 suggested_scenes、available_scenes

**实现：**
- `knowledge_db.py`：`get_available_scenes()`、`increment_scene_choice()`
- `memory_system.py`：`get_suggested_scenes_from_summary()`

**未来改进：** 智能排序、热门场景

---

## 四、核心数据流

```
用户登录
    → 初始化 memory/accounts/{用户名}/
    → 加载 user_profile、diary、session_temp

中文沟通
    → 用户输入（语音/文本）→ ASR/文本 → process_text()
    → 注入 memory_context + 角色 prompt → LLM 生成
    → 保存到 session_temp → TTS 播放

结束对话
    → 生成摘要 → 写入 diary
    → 抽取用户信息 → 更新 user_profile
    → 推荐场景 → 返回 available_scenes、suggested_scenes

生成英语卡片（口语训练库路径）
    → 用户选择场景 + 难度
    → oral_training_db.get_dialogue_record_for_user(scene, difficulty) 按 unit_practice 选下一批次
    → 返回 dialogue_lines + dialogue_id → 逐句 TTS → 保存音频

练习模式
    → 解析卡片 → 用户逐句复述
    → check_meaning_consistency() 校验
    → 练习结束后：generate-review（纠错用 AI，核心句型/语块与 Review 对话来自 DB）
    → save_practice_memory() → 更新 unit_practice（批次完成）
```

---

## 五、API 速查表

| 板块 | 方法 | 路径 | 用途 |
|------|------|------|------|
| 1 | POST | /api/account/login | 登录/创建 |
| 1 | GET | /api/account/current | 当前账号 |
| 1 | POST | /api/account/logout | 退出 |
| 3 | POST | /api/voice/upload | 语音上传转写 |
| 3 | POST | /api/text/send | 文本发送 |
| 5 | POST | /api/conversation/end | 结束对话、生成摘要 |
| 6 | POST | /api/english/generate | 生成英语卡片 |
| 7 | POST | /api/practice/start | 开始练习 |
| 7 | POST | /api/practice/respond | 练习回复校验 |
| 7 | POST | /api/practice/end | 结束练习 |
| 7 | POST | /api/practice/transcribe | 练习专用转写 |
| 8 | GET | /api/knowledge/available-scenes | 可选场景 |
| 8 | POST | /api/knowledge/select-scene | 记录场景选择 |
| 8 | GET | /api/knowledge/recommended | 推荐知识点 |
| 10 | POST | /api/user/update_english_level | 更新英文水平 |
| 10 | POST | /api/learning/start_english | 切换英文学习阶段 |
| 11 | POST | /api/practice/generate-review | 生成复习笔记（纠错+DB 核心句型/语块+Review 对话） |
| 12 | POST | /api/practice/save-memory | 更新练习进度（unit_practice） |

---

## 六、未来改进汇总

| 板块 | 改进方向 |
|------|----------|
| 1 账户 | 密码/认证、数据导入导出、多设备同步 |
| 2 中文沟通 | 更智能的信息抽取、兴趣标签、可配置触发词 |
| 3 语音输入 | 更多 ASR 提供商、VAD、实时转写 |
| 4 AI对话 | 更多 LLM、流式 TTS、多音色 |
| 5 摘要 | 多轮压缩、与知识图谱关联、敏感信息脱敏 |
| 6 英语卡片 | 难度自适应、自定义知识点、对话缓存 |
| 7 练习 | 发音评估、流利度分析、掌握度回写 knowledge_db |
| 8 知识库 | 增量同步、遗忘曲线、在线编辑 |
| 9 WebSocket | 心跳重连、多房间、消息持久化 |
| 10 难度 | 水平自测、分级推荐 |
| 11 复习笔记 | 与知识点 ID 关联、导出复习卡片 |
| 12 练习进度 | 遗忘曲线复习提醒、按 unit_practice 生成复习列表 |
| 13 场景选择 | 智能排序、热门场景 |
