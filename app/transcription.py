import os
import asyncio
# pyaudio 按需导入（服务端录音时使用）
import wave
import numpy as np
import aiohttp
import tempfile
# faster_whisper / torch 按需导入（仅本地 ASR 使用，豆包/OpenAI 路径不加载）
from dotenv import load_dotenv

# ANSI escape codes for colors
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'

# Load environment variables
load_dotenv()

# Get API keys and base URL
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
# API_PROVIDER将从app.py导入，以便支持动态切换
from .app import API_PROVIDER

# 初始化豆包ASR客户端（可选）
doubao_asr_client = None

try:
    from .doubao import DoubaoASRClient
    try:
        doubao_asr_client = DoubaoASRClient()
        print(f"{NEON_GREEN}豆包ASR客户端初始化成功{RESET_COLOR}")
    except ValueError as e:
        print(f"{YELLOW}豆包ASR客户端初始化失败: {e}{RESET_COLOR}")
    except Exception as e:
        print(f"{YELLOW}豆包ASR客户端初始化失败: {e}{RESET_COLOR}")
except ImportError as e:
    print(f"{YELLOW}无法导入豆包ASR客户端模块: {e}{RESET_COLOR}")

# Debug flag for audio levels
DEBUG_AUDIO_LEVELS = os.getenv("DEBUG_AUDIO_LEVELS", "false").lower() == "true"

# Check for local Faster Whisper setting
FASTER_WHISPER_LOCAL = os.getenv("FASTER_WHISPER_LOCAL", "true").lower() == "true"

# Initialize whisper model as None to lazy load
whisper_model = None

def initialize_whisper_model():
    """Initialize the Faster Whisper model - only called when needed (e.g. CLI local ASR)"""
    global whisper_model

    if whisper_model is not None:
        return whisper_model

    from faster_whisper import WhisperModel
    try:
        import torch
        device = "cuda" if (torch and torch.cuda.is_available()) else "cpu"
    except ImportError:
        device = "cpu"

    model_size = "medium.en"
    try:
        print(f"Attempting to load Faster-Whisper on {device}...")
        whisper_model = WhisperModel(model_size, device=device, compute_type="float16" if device == "cuda" else "int8")
        print("Faster-Whisper initialized successfully.")
    except Exception as e:
        print(f"Error initializing Faster-Whisper on {device}: {e}")
        print("Falling back to CPU mode...")
        model_size = "tiny.en"
        whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("Faster-Whisper initialized on CPU successfully.")

    return whisper_model

def transcribe_with_whisper(audio_file):
    """Transcribe audio using local Faster Whisper model"""
    # Lazy load the model only when needed
    model = initialize_whisper_model()
    
    segments, info = model.transcribe(audio_file, beam_size=5)
    transcription = ""
    for segment in segments:
        transcription += segment.text + " "
    return transcription.strip()

async def transcribe_with_doubao_file_asr(audio_url: str) -> str:
    """豆包录音文件识别大模型：提交音频 URL，轮询查询结果。无分段延迟，响应更快。"""
    app_key = os.getenv("VOLCENGINE_ASR_APP_ID", "").strip()
    access_key = os.getenv("VOLCENGINE_ASR_ACCESS_TOKEN", "").strip()
    # 1.0 常用 volc.bigasr.auc，2.0 为 volc.seedasr.auc；若报 45000030 未授权可改为 volc.bigasr.auc
    resource_id = os.getenv("VOLCENGINE_FILE_ASR_RESOURCE_ID", "volc.bigasr.auc").strip()
    base_url = os.getenv("VOLCENGINE_FILE_ASR_BASE_URL", "https://openspeech.bytedance.com").rstrip("/")
    if not app_key or not access_key:
        raise ValueError("请设置 VOLCENGINE_ASR_APP_ID 和 VOLCENGINE_ASR_ACCESS_TOKEN")
    submit_url = f"{base_url}/api/v3/auc/bigmodel/submit"
    query_url = f"{base_url}/api/v3/auc/bigmodel/query"
    task_id = __import__("uuid").uuid4().hex
    headers_submit = {
        "Content-Type": "application/json",
        "X-Api-App-Key": app_key,
        "X-Api-Access-Key": access_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": task_id,
        "X-Api-Sequence": "-1",
    }
    body = {
        "user": {"uid": "voice_chat_user"},
        "audio": {"url": audio_url, "format": "wav"},
        "request": {"model_name": "bigmodel", "enable_itn": True},
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(submit_url, json=body, headers=headers_submit) as resp:
            code = resp.headers.get("X-Api-Status-Code", "")
            if code != "20000000":
                msg = resp.headers.get("X-Api-Message", await resp.text())
                raise ValueError(f"录音文件识别提交失败: {code} - {msg}")
            x_tt_logid = resp.headers.get("X-Tt-Logid", "")
        headers_query = {
            "Content-Type": "application/json",
            "X-Api-App-Key": app_key,
            "X-Api-Access-Key": access_key,
            "X-Api-Resource-Id": resource_id,
            "X-Api-Request-Id": task_id,
            "X-Tt-Logid": x_tt_logid,
        }
        for _ in range(60):
            await asyncio.sleep(1)
            async with session.post(query_url, json={}, headers=headers_query) as qresp:
                code = qresp.headers.get("X-Api-Status-Code", "")
                if code == "20000000":
                    data = await qresp.json()
                    result = (data or {}).get("result") or {}
                    text = (result.get("text") or "").strip()
                    if text:
                        return text
                    raise ValueError("录音文件识别返回空文本（可能为静音或识别失败）")
                if code not in ("20000001", "20000002"):
                    msg = qresp.headers.get("X-Api-Message", await qresp.text())
                    raise ValueError(f"录音文件识别查询失败: {code} - {msg}")
        raise ValueError("录音文件识别查询超时")

async def transcribe_with_doubao_asr(audio_file):
    """已废弃：请使用 transcribe_with_doubao_file_asr(audio_url)。保留仅为兼容，实际应走录音文件识别。"""
    raise ValueError("豆包流式 ASR 已停用，请使用录音文件识别；调用方应传入 audio_url 并调用 transcribe_with_doubao_file_asr")

async def transcribe_with_openai_api(audio_file, model="gpt-4o-mini-transcribe"):
    """Transcribe audio using OpenAI's API
    
    Returns:
        str: 转录文本，如果失败则返回None
    """
    if not OPENAI_API_KEY:
        print("Error: OpenAI API密钥未配置，请在.env文件中设置OPENAI_API_KEY")
        return None
    
    # Construct API URL from base URL (support proxy APIs)
    # If OPENAI_BASE_URL is like "https://api.gptsapi.net/v1", use it directly
    # If it's like "https://api.openai.com/v1/chat/completions", extract base
    base_url = OPENAI_BASE_URL
    if "/chat/completions" in base_url:
        base_url = base_url.replace("/chat/completions", "")
    elif "/v1" not in base_url:
        base_url = base_url.rstrip("/") + "/v1"
    
    # Ensure base_url ends with /v1
    if not base_url.endswith("/v1"):
        if base_url.endswith("/"):
            base_url = base_url + "v1"
        else:
            base_url = base_url + "/v1"
    
    api_url = f"{base_url}/audio/transcriptions"
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(audio_file, "rb") as audio_file_data:
                form_data = aiohttp.FormData()
                form_data.add_field('file', 
                                    audio_file_data.read(),
                                    filename=os.path.basename(audio_file),
                                    content_type='audio/wav')
                
                # Use the model directly
                form_data.add_field('model', model)
                
                headers = {
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                }
                
                async with session.post(api_url, data=form_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        transcription = result.get("text", "")
                        return transcription
                    else:
                        error_text = await response.text()
                        print(f"Error: OpenAI ASR API调用失败 - HTTP {response.status}: {error_text}")
                        return None
    except Exception as e:
        print(f"Error: OpenAI ASR API调用失败 - {str(e)}")
        return None

def detect_silence(data, threshold=512, chunk_size=1024):
    """Detect silence in audio data"""
    audio_data = np.frombuffer(data, dtype=np.int16)
    level = np.mean(np.abs(audio_data))
    # Only print audio levels if debug is enabled
    if DEBUG_AUDIO_LEVELS:
        print(f"Audio level: {level}")
    return level < threshold

async def record_audio(file_path, silence_threshold=512, silence_duration=2.5, chunk_size=1024, send_status_callback=None):
    """Record audio to a file path

    Args:
        file_path: Path to save the recorded audio
        silence_threshold: Threshold for silence detection
        silence_duration: Duration of silence to stop recording
        chunk_size: Size of audio chunks
        send_status_callback: Callback to send status updates (optional)
    """
    import pyaudio
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=chunk_size)
    frames = []
    print("Recording...")
    
    # Notify frontend if callback provided
    if send_status_callback:
        await send_status_callback({"action": "recording_started"})
        
    silent_chunks = 0
    speaking_chunks = 0
    
    while True:
        data = stream.read(chunk_size, exception_on_overflow=False)
        frames.append(data)
        
        if detect_silence(data, threshold=silence_threshold, chunk_size=chunk_size):
            silent_chunks += 1
            if silent_chunks > silence_duration * (16000 / chunk_size):
                break
        else:
            silent_chunks = 0
            speaking_chunks += 1
            
        if speaking_chunks > silence_duration * (16000 / chunk_size) * 10:
            break
            
    print("Recording stopped.")
    
    # Notify frontend if callback provided
    if send_status_callback:
        await send_status_callback({"action": "recording_stopped"})
        
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf = wave.open(file_path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()

async def record_audio_enhanced(send_status_callback=None, silence_threshold=300, silence_duration=2.0):
    """Enhanced audio recording with waiting for speech detection

    Args:
        send_status_callback: Callback to send status messages
        silence_threshold: Threshold for silence detection
        silence_duration: Duration of silence to stop recording

    Returns:
        Path to the recorded audio file
    """
    import pyaudio
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_filename = temp_file.name
    temp_file.close()

    # Recording parameters
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    
    # Recording logic
    p = pyaudio.PyAudio()
    
    # Debug info about audio devices - only show once
    if DEBUG_AUDIO_LEVELS:
        print("\nAudio input devices:")
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:  # Only input devices
                print(f"Device {i}: {dev_info['name']}")
        print("Using default input device\n")
    
    # Open the stream with input_device_index=None to use default device
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    # Wait for user to start speaking
    print(YELLOW + "Waiting for speech..." + RESET_COLOR)
    if send_status_callback:
        await send_status_callback({"action": "waiting_for_speech"})
    
    # Flush initial buffer
    for _ in range(5):
        stream.read(CHUNK)
        
    initial_silent_chunks = 0
    silence_broken = False
    
    # Wait for user to start speaking
    while not silence_broken:
        data = stream.read(CHUNK, exception_on_overflow=False)
        if not detect_silence(data, threshold=silence_threshold):
            silence_broken = True
            print("Speech detected, recording started...")
            break
        
        initial_silent_chunks += 1
        # If waiting too long (15 seconds), abort
        if initial_silent_chunks > 15 * (RATE / CHUNK):
            print("No speech detected after timeout. Aborting.")
            stream.stop_stream()
            stream.close()
            p.terminate()
            try:
                os.unlink(temp_filename)
            except:
                pass
            if send_status_callback:
                await send_status_callback({
                    "action": "error", 
                    "message": "No speech detected. Please check your microphone and try again."
                })
            return None
            
        # Every 2 seconds, provide feedback
        if initial_silent_chunks % (2 * int(RATE / CHUNK)) == 0 and initial_silent_chunks > 0 and initial_silent_chunks % (4 * int(RATE / CHUNK)) == 0:
            if send_status_callback:
                # Just send a reminder ping, no need for message text as UI now handles this
                await send_status_callback({
                    "action": "waiting_for_speech"
                })
                
    # Now begin actual recording
    frames = []
    print("Enhanced recording...")
    if send_status_callback:
        await send_status_callback({"action": "recording_started"})
    
    # Add the initial speech chunk that broke the silence
    if silence_broken:
        frames.append(data)
    
    silent_chunks = 0
    speaking_chunks = 0
    
    # Continue recording until silence is detected
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        if detect_silence(data, threshold=silence_threshold):
            silent_chunks += 1
            if silent_chunks > silence_duration * (RATE / CHUNK):
                break
        else:
            silent_chunks = 0
            speaking_chunks += 1
        if speaking_chunks > silence_duration * (RATE / CHUNK) * 15:  # Allow longer recordings
            break
            
    print("Enhanced recording stopped.")
    if send_status_callback:
        await send_status_callback({"action": "recording_stopped"})
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # If no substantial recording was made, return None
    if len(frames) < 10:
        try:
            os.unlink(temp_filename)
        except:
            pass
        if send_status_callback:
            await send_status_callback({
                "action": "error", 
                "message": "Recording too short. Please try again."
            })
        return None
    
    # Save the recorded audio
    wf = wave.open(temp_filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return temp_filename

async def send_status_message(callback, message):
    """Helper function to send status messages through the callback
    
    This handles both dictionary and string message formats.
    
    Args:
        callback: The callback function to send the message through
        message: Either a dictionary or string message
    """
    if callback:
        await callback(message)

async def transcribe_audio(transcription_model="gpt-4o-mini-transcribe", use_local=False, send_status_callback=None, base_url=None):
    """Main function to record audio and transcribe it
    
    注意：use_local参数已废弃，现在只使用全局API_PROVIDER指定的供应商。豆包使用录音文件识别，需可公网访问的 base_url（或设置 PUBLIC_APP_URL）。
    
    Args:
        transcription_model: Model to use for OpenAI transcription (仅用于OpenAI)
        use_local: 已废弃，不再支持本地Faster Whisper
        send_status_callback: Callback to send status messages
        base_url: 可选，用于豆包录音文件识别的服务根 URL；未传时使用环境变量 PUBLIC_APP_URL
    
    Returns:
        Transcribed text or error message
    """
    try:
        # Create an async wrapper for the callback
        async def callback_wrapper(msg):
            if send_status_callback:
                await send_status_message(send_status_callback, msg)
                
        # Record audio with enhanced mode
        temp_filename = await record_audio_enhanced(
            send_status_callback=callback_wrapper
        )
        
        if not temp_filename:
            return None
            
        # 只使用全局API_PROVIDER指定的ASR供应商
        transcription = None
        if API_PROVIDER == 'doubao':
            # 豆包录音文件识别：本地录音已是 16kHz wav，仅需注册临时 URL 供火山拉取
            try:
                from .audio_temp import register_audio_temp, unregister_audio_temp
                base = (base_url or os.getenv("PUBLIC_APP_URL", "")).strip().rstrip("/")
                if not base:
                    raise ValueError("豆包录音文件识别需要可公网访问的 base_url，请在调用时传入 base_url 或设置环境变量 PUBLIC_APP_URL")
                token = register_audio_temp(temp_filename)
                try:
                    audio_url = f"{base}/api/audio/temp/{token}"
                    transcription = await transcribe_with_doubao_file_asr(audio_url)
                finally:
                    unregister_audio_temp(token)
            except Exception as e:
                if send_status_callback:
                    await send_status_message(send_status_callback, {
                        "action": "error",
                        "message": str(e)
                    })
                return str(e)
            if transcription is None:
                error_msg = "Error: 豆包录音文件识别未返回结果，请检查环境变量与网络"
                print(error_msg)
                if send_status_callback:
                    await send_status_message(send_status_callback, {
                        "action": "error",
                        "message": error_msg
                    })
                return error_msg
        elif API_PROVIDER == 'openai':
            # Use OpenAI API
            if not OPENAI_API_KEY:
                error_msg = "Error: OpenAI API密钥未配置，请在.env文件中设置OPENAI_API_KEY"
                print(error_msg)
                if send_status_callback:
                    await send_status_message(send_status_callback, {
                        "action": "error",
                        "message": error_msg
                    })
                return error_msg
            transcription = await transcribe_with_openai_api(temp_filename, transcription_model)
            if transcription is None:
                error_msg = "Error: OpenAI ASR API调用失败"
                print(error_msg)
                if send_status_callback:
                    await send_status_message(send_status_callback, {
                        "action": "error",
                        "message": error_msg
                    })
                return error_msg
        else:
            error_msg = f"Error: 不支持的API供应商 '{API_PROVIDER}'，仅支持 'doubao' 或 'openai'"
            print(error_msg)
            if send_status_callback:
                await send_status_message(send_status_callback, {
                    "action": "error",
                    "message": error_msg
                })
            return error_msg
            
        # Clean up temp file
        try:
            os.unlink(temp_filename)
        except Exception as e:
            print(f"Error removing temporary file: {e}")
            
        return transcription
        
    except Exception as e:
        error_msg = f"Error: ASR调用失败 - {str(e)}"
        print(error_msg)
        if send_status_callback:
            await send_status_message(send_status_callback, {
                "action": "error", 
                "message": error_msg
            })
        return error_msg 