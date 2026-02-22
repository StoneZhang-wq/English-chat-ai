# 环境变量说明：本地 .env 与 Railway 变量

## 一、本地 .env 需要「按环境」改的项

| 变量 | 本地建议 | 说明 |
|------|----------|------|
| `PUBLIC_APP_URL` | **注释掉或留空** | 本地用 request 的 host；豆包录音识别会失败（除非用 ngrok） |
| `PUBLIC_APP_URL` | Railway 上**必填** | 见下方 Railway 清单 |

其余和当前功能相关的项（豆包 LLM/TTS/ASR、Supabase 等）本地可以和 Railway 一致，或按需改。

---

## 二、Railway 上必须配置的变量（按你当前豆包 + Supabase 方案）

以下**建议全部**在 Railway 项目 → Variables 里配置（值用你在 .env 里的，不要提交 .env 到 git）。

### 1. 全局 / 模型与语音供应商

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `API_PROVIDER` | `doubao` | 与 MODEL_PROVIDER 一致，对话/ASR 用豆包 |
| `MODEL_PROVIDER` | `doubao` | LLM 用豆包 |
| `TTS_PROVIDER` | `doubao` | TTS 用豆包 |
| `ASR_PROVIDER` | `doubao` | 语音识别用豆包 |

### 2. 豆包 LLM（方舟）

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `DOUBAO_API_KEY` | 你的方舟 API Key | 必填 |
| `DOUBAO_API_BASE_URL` | `https://ark.cn-beijing.volces.com/api/v3` | 可选，有默认 |
| `LLM_MODEL` | `doubao-seed-2-0-mini-260215` | 2.0 Mini 260215 |
| `DOUBAO_REASONING_EFFORT` | `minimal` | 可选，默认 minimal（最快） |

### 3. 豆包 TTS

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `VOLCENGINE_APP_ID` | 你的 App ID | 与 ASR 通常相同 |
| `VOLCENGINE_ACCESS_TOKEN` | 你的 Access Token | 与 ASR 通常相同 |
| `TTS_VOICE_TYPE` | `en_male_smith_mars_bigtts` | 英文主音色 |
| `TTS_VOICE_TYPE_B` | `en_female_sarah_mars_bigtts` | 英文角色 B |
| `TTS_VOICE_TYPE_ZH` | `zh_female_cancan_mars_bigtts` | 中文音色 |
| `TTS_ENCODING` | `mp3` | 可选 |

### 4. 豆包 ASR（录音文件识别）

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `VOLCENGINE_ASR_APP_ID` | 同 TTS 的 App ID | 必填 |
| `VOLCENGINE_ASR_ACCESS_TOKEN` | 同 TTS 的 Token | 必填 |
| `VOLCENGINE_FILE_ASR_RESOURCE_ID` | `volc.bigasr.auc` | 1.0 资源；2.0 用 volc.seedasr.auc |

### 5. 公网访问（录音识别必填）

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `PUBLIC_APP_URL` | `https://englishchatcommunity.com` | **必填**，不要末尾斜杠；豆包拉临时音频用 |

### 6. Supabase（用户记忆）

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `MEMORY_BACKEND` | `supabase` | 用 Supabase 时必填 |
| `SUPABASE_URL` | 你的 Supabase 项目 URL | 必填 |
| `SUPABASE_SERVICE_ROLE_KEY` | 你的 service_role key | 必填 |

### 7. 可选（有代码内默认）

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `MAX_CHAR_LENGTH` | `3000` | 回复/音频长度上限 |
| `VOICE_SPEED` | `1.2` | 语速 |
| `CHARACTER_NAME` | `english_tutor` | 默认角色名 |

---

## 三、复制清单（仅变量名，便于在 Railway 里逐条添加）

```
API_PROVIDER
MODEL_PROVIDER
TTS_PROVIDER
ASR_PROVIDER
DOUBAO_API_KEY
DOUBAO_API_BASE_URL
LLM_MODEL
DOUBAO_REASONING_EFFORT
VOLCENGINE_APP_ID
VOLCENGINE_ACCESS_TOKEN
TTS_VOICE_TYPE
TTS_VOICE_TYPE_B
TTS_VOICE_TYPE_ZH
TTS_ENCODING
VOLCENGINE_ASR_APP_ID
VOLCENGINE_ASR_ACCESS_TOKEN
VOLCENGINE_FILE_ASR_RESOURCE_ID
PUBLIC_APP_URL
MEMORY_BACKEND
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
MAX_CHAR_LENGTH
VOICE_SPEED
CHARACTER_NAME
```

值从你本地 `.env` 里复制即可；**注意**：`PUBLIC_APP_URL` 在 Railway 上必须设为你的公网域名（如 `https://englishchatcommunity.com`）。
