# 豆包API集成说明

本项目已集成豆包（Doubao）的LLM、TTS、ASR API，您可以通过环境变量选择使用OpenAI或豆包的API。

## 环境变量配置

在项目的 `.env` 文件中添加以下配置：

### 1. 选择API提供商

```env
# 选择LLM提供商：openai 或 doubao
MODEL_PROVIDER=openai

# 选择TTS提供商：openai, elevenlabs, kokoro, sparktts, doubao
TTS_PROVIDER=openai

# 选择ASR提供商：openai 或 doubao
ASR_PROVIDER=openai
```

### 2. 豆包LLM配置

```env
# 豆包API密钥（必需）
DOUBAO_API_KEY=your_api_key_here

# 豆包API基础URL（可选，默认值如下）
DOUBAO_API_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 豆包LLM模型ID（必需，替换为你的模型ID）
LLM_MODEL=ep-20241220123456-abcde
```

### 3. 豆包TTS配置（火山引擎）

```env
# TTS应用ID（必需）
VOLCENGINE_APP_ID=your_app_id

# TTS访问令牌（必需）
VOLCENGINE_ACCESS_TOKEN=your_access_token

# TTS端点（可选，默认值如下）
TTS_ENDPOINT=wss://openspeech.bytedance.com/api/v1/tts/ws_binary

# TTS音色类型（可选，默认值如下）
TTS_VOICE_TYPE=zh_female_cancan_mars_bigtts

# TTS编码格式（可选，mp3 或 wav，默认 mp3）
TTS_ENCODING=mp3
```

### 4. 豆包ASR配置（火山引擎）

```env
# ASR应用ID（必需）
# 注意：在API请求头中，VOLCENGINE_ASR_APP_ID 作为 X-Api-App-Key
VOLCENGINE_ASR_APP_ID=your_asr_app_id

# ASR访问令牌（必需）
# 注意：在API请求头中，VOLCENGINE_ASR_ACCESS_TOKEN 作为 X-Api-Access-Key
VOLCENGINE_ASR_ACCESS_TOKEN=your_asr_access_token

# ASR端点（可选，默认值如下）
# bigmodel: 流式识别（适用于实时录音流式上传）
# bigmodel_nostream: 非流式识别（适用于一次性上传完整音频文件）
# 前端实时录音建议使用 bigmodel（流式）
ASR_ENDPOINT=wss://openspeech.bytedance.com/api/v3/sauc/bigmodel

# ASR分段时长（可选，默认200ms）
ASR_SEGMENT_DURATION=200
```

## 使用方法

### 1. 使用豆包LLM

在 `.env` 文件中设置：
```env
MODEL_PROVIDER=doubao
DOUBAO_API_KEY=your_api_key_here
LLM_MODEL=your_model_id
```

### 2. 使用豆包TTS

在 `.env` 文件中设置：
```env
TTS_PROVIDER=doubao
VOLCENGINE_APP_ID=your_app_id
VOLCENGINE_ACCESS_TOKEN=your_access_token
```

### 3. 使用豆包ASR

在 `.env` 文件中设置：
```env
ASR_PROVIDER=doubao
VOLCENGINE_ASR_APP_ID=your_asr_app_id
VOLCENGINE_ASR_ACCESS_TOKEN=your_asr_access_token
```

## 注意事项

1. **API密钥获取**：
   - 豆包LLM：需要在豆包控制台创建应用并获取API密钥
   - 豆包TTS/ASR：需要在火山引擎控制台创建应用并获取App ID和Access Token

2. **模型ID**：
   - LLM_MODEL 需要替换为你实际创建的模型端点ID（格式如：ep-20241220123456-abcde）

3. **音频格式要求**：
   - ASR要求：WAV格式，16kHz采样率，16bit位深，单声道
   - TTS输出：默认MP3格式，可通过TTS_ENCODING配置

4. **兼容性**：
   - 原有功能完全保留，不影响现有OpenAI、ElevenLabs等API的使用
   - 可以混合使用不同提供商的API（例如：OpenAI LLM + 豆包TTS）

5. **错误处理**：
   - 如果豆包客户端初始化失败，系统会自动回退到默认提供商
   - 错误信息会在控制台和前端显示

## 测试

启动应用后，检查控制台输出：
- 如果看到 "豆包LLM客户端初始化成功"，说明LLM配置正确
- 如果看到 "豆包TTS客户端初始化成功"，说明TTS配置正确
- 如果看到 "豆包ASR客户端初始化成功"，说明ASR配置正确

如果看到警告信息，请检查对应的环境变量配置。
