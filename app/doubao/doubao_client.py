"""
豆包API客户端
"""
import requests
import json
import time
import uuid
import asyncio
import struct
import gzip
import io
from typing import Optional, List, Dict
import websockets
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Config from environment variables
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")
DOUBAO_API_BASE_URL = os.getenv("DOUBAO_API_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
LLM_MODEL = os.getenv("LLM_MODEL")
VOLCENGINE_APP_ID = os.getenv("VOLCENGINE_APP_ID")
VOLCENGINE_ACCESS_TOKEN = os.getenv("VOLCENGINE_ACCESS_TOKEN")
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", "wss://openspeech.bytedance.com/api/v1/tts/ws_binary")
TTS_VOICE_TYPE = os.getenv("TTS_VOICE_TYPE", "zh_female_cancan_mars_bigtts")
TTS_ENCODING = os.getenv("TTS_ENCODING", "mp3")
VOLCENGINE_ASR_APP_ID = os.getenv("VOLCENGINE_ASR_APP_ID")
VOLCENGINE_ASR_ACCESS_TOKEN = os.getenv("VOLCENGINE_ASR_ACCESS_TOKEN")
ASR_ENDPOINT = os.getenv("ASR_ENDPOINT", "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel")
ASR_SEGMENT_DURATION = int(os.getenv("ASR_SEGMENT_DURATION", "200"))


class DoubaoLLMClient:
    """豆包LLM客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or DOUBAO_API_KEY
        self.base_url = base_url or DOUBAO_API_BASE_URL
        self.model = model or LLM_MODEL
        
        if not self.api_key:
            raise ValueError("请设置DOUBAO_API_KEY环境变量")
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = None, stream: bool = False) -> Optional[str]:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制回复的随机性（与OpenAI保持一致）
            max_tokens: 最大生成token数（对应OpenAI的max_completion_tokens，用于控制输出长度）
            stream: 是否使用流式响应（与OpenAI保持一致，提升响应速度）
        
        Returns:
            AI回复内容（流式模式下返回完整内容）
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        # 添加max_tokens参数（如果提供），与OpenAI保持一致
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        # 添加stream参数，启用流式响应（关键优化）
        if stream:
            data["stream"] = True
        
        # 添加详细调试日志，打印实际发送的payload（摘要）
        print(f"Debug: Doubao API Request Payload:")
        print(f"  - Model: {self.model}")
        print(f"  - Temperature: {temperature}")
        print(f"  - Max Tokens: {max_tokens}")
        print(f"  - Stream: {stream}")
        print(f"  - Messages count: {len(messages)}")
        if messages:
            print(f"  - System message length: {len(messages[0].get('content', ''))} chars")
            print(f"  - User message: {messages[-1].get('content', '')[:100]}..." if len(messages) > 0 and len(messages[-1].get('content', '')) > 100 else f"  - User message: {messages[-1].get('content', '') if messages else ''}")
        
        try:
            import time
            start_time = time.time()
            
            # 统一超时时间为45秒，与OpenAI保持一致
            if stream:
                # 流式响应模式：边接收边处理，提升响应速度
                response = requests.post(url, headers=headers, json=data, stream=True, timeout=45)
                response.raise_for_status()
                
                full_response = ""
                json_buffer = ""  # 用于累积可能跨行的JSON
                first_chunk_time = None
                brace_count = 0  # 用于跟踪JSON对象的完整性
                
                # 使用iter_lines，累积JSON直到找到完整的对象
                for line_bytes in response.iter_lines(decode_unicode=False):
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                        print(f"Debug: Doubao first chunk received in {first_chunk_time - start_time:.2f}s")
                    
                    if not line_bytes:
                        # 空行，尝试解析累积的buffer
                        if json_buffer.strip():
                            try:
                                chunk = json.loads(json_buffer.strip())
                                json_buffer = ""
                                brace_count = 0
                                
                                # 提取content
                                delta_content = ""
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    choice = chunk["choices"][0]
                                    if "delta" in choice:
                                        delta = choice["delta"]
                                        # 只提取content字段，忽略reasoning_content（推理过程）
                                        delta_content = delta.get("content", "")
                                    
                                    if not delta_content and "message" in choice:
                                        delta_content = choice["message"].get("content", "")
                                
                                if delta_content:
                                    full_response += delta_content
                            except json.JSONDecodeError:
                                pass
                        continue
                    
                    # 解码为字符串
                    try:
                        line_text = line_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        continue
                    
                    # 处理SSE格式（data: 开头）
                    if line_text.startswith("data:"):
                        line_text = line_text[5:].strip()
                    
                    if not line_text or line_text == "[DONE]":
                        continue
                    
                    # 累积到buffer
                    json_buffer += line_text
                    
                    # 计算大括号数量，判断JSON是否完整
                    brace_count += line_text.count('{') - line_text.count('}')
                    
                    # 如果大括号平衡，尝试解析
                    if brace_count == 0 and json_buffer.strip():
                        try:
                            chunk = json.loads(json_buffer.strip())
                            json_buffer = ""
                            brace_count = 0
                            
                            # 提取content
                            delta_content = ""
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                choice = chunk["choices"][0]
                                if "delta" in choice:
                                    delta = choice["delta"]
                                    # 只提取content字段，忽略reasoning_content
                                    delta_content = delta.get("content", "")
                                
                                if not delta_content and "message" in choice:
                                    delta_content = choice["message"].get("content", "")
                            
                            if delta_content:
                                full_response += delta_content
                        except json.JSONDecodeError:
                            # 解析失败，继续累积
                            pass
                
                # 处理剩余的buffer
                if json_buffer.strip():
                    try:
                        chunk = json.loads(json_buffer.strip())
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            choice = chunk["choices"][0]
                            if "delta" in choice:
                                delta_content = choice["delta"].get("content", "")
                                if delta_content:
                                    full_response += delta_content
                    except json.JSONDecodeError:
                        pass
                
                total_time = time.time() - start_time
                print(f"Debug: Doubao stream complete in {total_time:.2f}s, response length: {len(full_response)}")
                return full_response
            else:
                # 非流式模式（向后兼容）
                response = requests.post(url, headers=headers, json=data, timeout=45)
                response.raise_for_status()
                
                result = response.json()
                
                total_time = time.time() - start_time
                print(f"Debug: Doubao non-stream complete in {total_time:.2f}s")
                
                # 提取回复内容
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"API响应格式异常: {result}")
                    return None
                
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"错误详情: {error_detail}")
                except:
                    print(f"响应内容: {e.response.text}")
            return None


class DoubaoASRClient:
    """豆包ASR客户端（火山引擎 - WebSocket）"""
    
    # 协议常量
    PROTOCOL_VERSION = 0b0001
    MSG_TYPE_CLIENT_FULL_REQUEST = 0b0001
    MSG_TYPE_CLIENT_AUDIO_ONLY_REQUEST = 0b0010
    MSG_TYPE_SERVER_FULL_RESPONSE = 0b1001
    MSG_TYPE_SERVER_ERROR_RESPONSE = 0b1111
    FLAGS_POS_SEQUENCE = 0b0001
    FLAGS_NEG_WITH_SEQUENCE = 0b0011
    SERIALIZATION_JSON = 0b0001
    SERIALIZATION_NONE = 0b0000
    COMPRESSION_GZIP = 0b0001
    
    def __init__(self, app_id: str = None, access_token: str = None, 
                 endpoint: str = None, segment_duration: int = None):
        # 注意：在API请求头中，app_id 作为 app_key，access_token 作为 access_key
        self.app_id = app_id or VOLCENGINE_ASR_APP_ID
        self.access_token = access_token or VOLCENGINE_ASR_ACCESS_TOKEN
        self.app_key = self.app_id  # API请求头中使用
        self.access_key = self.access_token  # API请求头中使用
        self.endpoint = endpoint or ASR_ENDPOINT
        self.segment_duration = segment_duration or ASR_SEGMENT_DURATION
        
        if not self.app_id or not self.access_token:
            raise ValueError("请设置VOLCENGINE_ASR_APP_ID和VOLCENGINE_ASR_ACCESS_TOKEN环境变量")
    
    def _gzip_compress(self, data: bytes) -> bytes:
        """Gzip压缩"""
        return gzip.compress(data)
    
    def _gzip_decompress(self, data: bytes) -> bytes:
        """Gzip解压"""
        return gzip.decompress(data)
    
    def _build_header(self, message_type: int, flags: int, 
                     serialization: int, compression: int) -> bytes:
        """构建消息头"""
        header = bytearray()
        header.append((self.PROTOCOL_VERSION << 4) | 1)  # version + header_size
        header.append((message_type << 4) | flags)  # message_type + flags
        header.append((serialization << 4) | compression)  # serialization + compression
        header.append(0x00)  # reserved
        return bytes(header)
    
    def _build_full_client_request(self, seq: int) -> bytes:
        """构建完整客户端请求"""
        header = self._build_header(
            self.MSG_TYPE_CLIENT_FULL_REQUEST,
            self.FLAGS_POS_SEQUENCE,
            self.SERIALIZATION_JSON,
            self.COMPRESSION_GZIP
        )
        
        # 根据端点类型判断是否为流式
        # bigmodel: 流式端点，enable_nonstream=False
        # bigmodel_nostream: 非流式端点，enable_nonstream=True
        is_streaming = "bigmodel_nostream" not in self.endpoint
        
        payload = {
            "user": {
                "uid": "demo_uid"
            },
            "audio": {
                "format": "wav",
                "codec": "raw",
                "rate": 16000,
                "bits": 16,
                "channel": 1
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "enable_ddc": True,
                "show_utterances": True,
                "enable_nonstream": not is_streaming  # 流式=False, 非流式=True
            }
        }
        
        print(f"ASR请求配置: 端点={self.endpoint}, 流式={is_streaming}, enable_nonstream={payload['request']['enable_nonstream']}")
        
        payload_bytes = json.dumps(payload).encode('utf-8')
        print(f"ASR请求payload (JSON): {json.dumps(payload, ensure_ascii=False)}")
        compressed_payload = self._gzip_compress(payload_bytes)
        print(f"压缩后payload大小: {len(compressed_payload)} 字节")
        
        request = bytearray()
        request.extend(header)
        request.extend(struct.pack('>i', seq))  # sequence
        request.extend(struct.pack('>I', len(compressed_payload)))  # payload size
        request.extend(compressed_payload)
        
        print(f"完整请求大小: {len(request)} 字节")
        return bytes(request)
    
    def _build_audio_only_request(self, seq: int, audio_data: bytes, is_last: bool = False) -> bytes:
        """构建音频请求"""
        # 保存原始seq用于日志（不修改传入的seq，避免影响外部逻辑）
        original_seq = seq
        
        # 根据is_last设置flags和seq
        if is_last:
            flags = self.FLAGS_NEG_WITH_SEQUENCE
            # 最后一个包：seq设为负值
            seq_for_packet = -seq
        else:
            flags = self.FLAGS_POS_SEQUENCE
            seq_for_packet = seq
        
        header = self._build_header(
            self.MSG_TYPE_CLIENT_AUDIO_ONLY_REQUEST,
            flags,
            self.SERIALIZATION_NONE,
            self.COMPRESSION_GZIP
        )
        
        compressed_audio = self._gzip_compress(audio_data)
        print(f"音频数据: 原始={len(audio_data)}字节, 压缩后={len(compressed_audio)}字节, is_last={is_last}, 原始seq={original_seq}, 发送seq={seq_for_packet}")
        
        request = bytearray()
        request.extend(header)
        request.extend(struct.pack('>i', seq_for_packet))  # 使用处理后的seq
        request.extend(struct.pack('>I', len(compressed_audio)))
        request.extend(compressed_audio)
        
        return bytes(request)
    
    def _parse_response(self, msg: bytes) -> Dict:
        """解析服务器响应"""
        if len(msg) < 4:
            return {"error": "消息太短"}
        
        header_size = msg[0] & 0x0f
        message_type = msg[1] >> 4
        flags = msg[1] & 0x0f
        serialization = msg[2] >> 4
        compression = msg[2] & 0x0f
        
        payload = msg[header_size * 4:]
        result = {
            "message_type": message_type,
            "flags": flags,
            "is_last": bool(flags & 0x02),
            "sequence": 0,
            "error_code": 0,
            "payload": None
        }
        
        # 解析message_type_specific_flags（按照示例代码的顺序）
        # 先解析sequence（如果flags & 0x01）
        if flags & 0x01:
            if len(payload) >= 4:
                result["sequence"] = struct.unpack('>i', payload[:4])[0]
                payload = payload[4:]
        
        # 检查is_last标志（flags & 0x02）
        if flags & 0x02:
            result["is_last"] = True
        
        # 解析message_type相关的数据
        if message_type == self.MSG_TYPE_SERVER_FULL_RESPONSE:
            # Full server response: 先解析payload size
            if len(payload) >= 4:
                payload_size = struct.unpack('>I', payload[:4])[0]
                payload = payload[4:]
                if len(payload) >= payload_size:
                    payload = payload[:payload_size]
                else:
                    print(f"警告: payload大小不匹配，期望{payload_size}字节，实际{len(payload)}字节")
        elif message_type == self.MSG_TYPE_SERVER_ERROR_RESPONSE:
            # Error response: 先解析error code，再解析payload size
            if len(payload) >= 8:
                result["error_code"] = struct.unpack('>i', payload[:4])[0]
                payload_size = struct.unpack('>I', payload[4:8])[0]
                payload = payload[8:]
                if len(payload) >= payload_size:
                    payload = payload[:payload_size]
                else:
                    print(f"警告: error payload大小不匹配，期望{payload_size}字节，实际{len(payload)}字节")
        
        # 解压缩
        if compression == self.COMPRESSION_GZIP and payload:
            try:
                payload = self._gzip_decompress(payload)
            except:
                pass
        
        # 解析JSON
        if serialization == self.SERIALIZATION_JSON and payload:
            try:
                result["payload"] = json.loads(payload.decode('utf-8'))
            except:
                pass
        
        return result
    
    def _extract_wav_data(self, wav_bytes: bytes) -> bytes:
        """从WAV文件中提取音频数据"""
        if len(wav_bytes) < 44:
            raise ValueError("WAV文件太短")
        
        # 解析WAV头信息
        sample_rate = struct.unpack('<I', wav_bytes[24:28])[0]
        num_channels = struct.unpack('<H', wav_bytes[22:24])[0]
        bits_per_sample = struct.unpack('<H', wav_bytes[34:36])[0]
        audio_format = struct.unpack('<H', wav_bytes[20:22])[0]
        byte_rate = struct.unpack('<I', wav_bytes[28:32])[0]
        block_align = struct.unpack('<H', wav_bytes[32:34])[0]
        
        print(f"WAV文件信息:")
        print(f"  音频格式: {audio_format} (1=PCM)")
        print(f"  声道数: {num_channels}")
        print(f"  采样率: {sample_rate}Hz")
        print(f"  字节率: {byte_rate} bytes/sec")
        print(f"  块对齐: {block_align} bytes")
        print(f"  位深: {bits_per_sample}bit")
        
        if audio_format != 1:
            raise ValueError(f"不支持的音频格式: {audio_format} (需要PCM格式=1)")
        if sample_rate != 16000:
            raise ValueError(f"采样率不正确: {sample_rate}Hz (需要16000Hz)")
        if num_channels != 1:
            raise ValueError(f"声道数不正确: {num_channels} (需要单声道=1)")
        if bits_per_sample != 16:
            raise ValueError(f"位深不正确: {bits_per_sample}bit (需要16bit)")
        
        # 验证块对齐
        expected_block_align = num_channels * (bits_per_sample // 8)
        if block_align != expected_block_align:
            print(f"警告: 块对齐不匹配，期望={expected_block_align}, 实际={block_align}")
        
        # 验证字节率
        expected_byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
        if byte_rate != expected_byte_rate:
            print(f"警告: 字节率不匹配，期望={expected_byte_rate}, 实际={byte_rate}")
        
        # 查找data子块
        pos = 36
        while pos < len(wav_bytes) - 8:
            subchunk_id = wav_bytes[pos:pos+4]
            subchunk_size = struct.unpack('<I', wav_bytes[pos+4:pos+8])[0]
            print(f"检查子块: {subchunk_id.decode('ascii', errors='ignore')}, 大小={subchunk_size}")
            if subchunk_id == b'data':
                audio_data = wav_bytes[pos+8:pos+8+subchunk_size]
                print(f"找到data子块，位置={pos}, 声明大小={subchunk_size}字节, 实际提取={len(audio_data)}字节")
                if len(audio_data) != subchunk_size:
                    print(f"警告: data子块大小不匹配！")
                return audio_data
            pos += 8 + subchunk_size
        
        raise ValueError("未找到data子块")
    
    def _split_audio(self, audio_data: bytes, segment_size: int) -> List[bytes]:
        """分割音频数据"""
        if segment_size <= 0:
            return [audio_data]
        
        segments = []
        for i in range(0, len(audio_data), segment_size):
            segments.append(audio_data[i:i+segment_size])
        return segments
    
    async def _transcribe_async(self, audio_data: bytes) -> Optional[str]:
        """
        语音转文字（异步实现）
        
        Args:
            audio_data: WAV格式的音频数据（16kHz, 16bit, 单声道）
        
        Returns:
            转录文本
        """
        if not audio_data:
            return None
        
        # 验证WAV格式
        if len(audio_data) < 44:
            print(f"WAV文件太短: {len(audio_data)} 字节")
            return None
        
        if audio_data[:4] != b'RIFF' or audio_data[8:12] != b'WAVE':
            print(f"不是有效的WAV文件，前12字节: {audio_data[:12]}")
            return None
        
        # 关键修复：根据示例代码，应该发送完整的WAV文件内容，而不是只提取data子块
        # 示例代码中split_audio是对完整WAV文件进行分段的
        # 验证WAV格式
        sample_rate = struct.unpack('<I', audio_data[24:28])[0]
        num_channels = struct.unpack('<H', audio_data[22:24])[0]
        bits_per_sample = struct.unpack('<H', audio_data[34:36])[0]
        audio_format = struct.unpack('<H', audio_data[20:22])[0]
        
        print(f"WAV文件信息:")
        print(f"  音频格式: {audio_format} (1=PCM)")
        print(f"  声道数: {num_channels}")
        print(f"  采样率: {sample_rate}Hz")
        print(f"  位深: {bits_per_sample}bit")
        print(f"  文件总大小: {len(audio_data)} 字节")
        
        if audio_format != 1:
            raise ValueError(f"不支持的音频格式: {audio_format} (需要PCM格式=1)")
        if sample_rate != 16000:
            raise ValueError(f"采样率不正确: {sample_rate}Hz (需要16000Hz)")
        if num_channels != 1:
            raise ValueError(f"声道数不正确: {num_channels} (需要单声道=1)")
        if bits_per_sample != 16:
            raise ValueError(f"位深不正确: {bits_per_sample}bit (需要16bit)")
        
        # 计算分段大小（基于音频数据部分，不包括WAV头）
        # 16kHz * 2 bytes * 0.2s = 6400 bytes
        segment_size = 16000 * 2 * self.segment_duration // 1000
        
        # 关键修复：使用完整的WAV文件内容进行分段（与示例代码一致）
        # 示例代码中split_audio是对完整WAV文件进行分段的
        print(f"使用完整WAV文件进行分段，文件大小: {len(audio_data)} 字节，分段大小: {segment_size} 字节")
        audio_segments = self._split_audio(audio_data, segment_size)
        print(f"音频分段: 文件大小={len(audio_data)}字节, 分段大小={segment_size}字节, 分段数={len(audio_segments)}")
        if len(audio_segments) > 0:
            print(f"第一段大小: {len(audio_segments[0])}字节, 最后一段大小: {len(audio_segments[-1])}字节")
        
        # 构建认证头
        headers = {
            "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
            "X-Api-Request-Id": str(uuid.uuid4()),
            "X-Api-Access-Key": self.access_key,
            "X-Api-App-Key": self.app_key
        }
        print(f"ASR WebSocket连接: endpoint={self.endpoint}")
        print(f"认证头: app_key={self.app_key[:10]}..., access_key={self.access_key[:10]}...")
        
        seq = 1
        transcript_text = ""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.endpoint, headers=headers) as ws:
                    print("WebSocket连接成功")
                    # 1. 发送完整客户端请求
                    full_request = self._build_full_client_request(seq)
                    print(f"发送完整客户端请求，大小={len(full_request)}字节")
                    await ws.send_bytes(full_request)
                    seq += 1
                    
                    # 接收初始响应
                    print("等待初始响应...")
                    msg = await ws.receive()
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        response = self._parse_response(msg.data)
                        print(f"ASR初始响应: {response}")
                        if response.get("error_code") != 0:
                            error_code = response.get('error_code')
                            error_msg = response.get("payload", {}).get("message", "未知错误") if isinstance(response.get("payload"), dict) else "未知错误"
                            print(f"ASR错误码: {error_code}, 错误信息: {error_msg}")
                            # 错误码映射
                            error_map = {
                                45000151: "音频格式不正确",
                                45000002: "空音频",
                                45000081: "等包超时",
                                45000001: "请求参数无效"
                            }
                            error_desc = error_map.get(error_code, f"错误码: {error_code}")
                            raise Exception(f"ASR API错误: {error_desc} - {error_msg}")
                    
                    # 2. 并发发送音频和接收响应（关键修复：使用并发方式）
                    print(f"开始发送音频数据包，共{len(audio_segments)}段")
                    
                    # 发送任务
                    async def send_audio_segments():
                        nonlocal seq
                        for i, segment in enumerate(audio_segments):
                            is_last = (i == len(audio_segments) - 1)
                            # 保存原始seq用于打印
                            original_seq = seq
                            audio_request = self._build_audio_only_request(seq, segment, is_last)
                            print(f"发送音频段 {i+1}/{len(audio_segments)}, 大小={len(segment)}字节, is_last={is_last}, seq={original_seq}")
                            await ws.send_bytes(audio_request)
                            
                            # 每个包发送后都等待（包括最后一个），模拟实时流
                            await asyncio.sleep(self.segment_duration / 1000)
                            
                            if not is_last:
                                seq += 1
                    
                    # 接收任务
                    async def receive_responses():
                        nonlocal transcript_text
                        while True:
                            try:
                                msg = await ws.receive()
                                
                                if msg.type == aiohttp.WSMsgType.BINARY:
                                    response = self._parse_response(msg.data)
                                    
                                    if response.get("error_code") != 0:
                                        error_code = response.get('error_code')
                                        payload = response.get("payload")
                                        print(f"ASR错误响应完整内容: {json.dumps(response, ensure_ascii=False, indent=2)}")
                                        
                                        # 尝试提取错误信息
                                        if isinstance(payload, dict):
                                            error_msg = (payload.get("message") or 
                                                        payload.get("error") or 
                                                        payload.get("error_msg") or
                                                        json.dumps(payload, ensure_ascii=False))
                                        elif payload:
                                            error_msg = str(payload)
                                        else:
                                            error_msg = "未知错误"
                                        
                                        # 确保error_msg是字符串
                                        if not isinstance(error_msg, str):
                                            error_msg = json.dumps(error_msg, ensure_ascii=False) if isinstance(error_msg, dict) else str(error_msg)
                                        
                                        print(f"ASR错误码: {error_code}, 错误信息: {error_msg}")
                                        # 错误码映射
                                        error_map = {
                                            45000151: "音频格式不正确",
                                            45000002: "空音频",
                                            45000081: "等包超时",
                                            45000001: "请求参数无效"
                                        }
                                        error_desc = error_map.get(error_code, f"错误码: {error_code}")
                                        raise Exception(f"ASR API错误: {error_desc} - {error_msg}")
                                    
                                    # 只使用 is_last 的最终结果，避免流式中间结果重复拼接成「你好你好你好...」
                                    payload = response.get("payload")
                                    is_last = response.get("is_last", False)
                                    if payload and isinstance(payload, dict):
                                        text = None
                                        if payload.get("text"):
                                            text = payload.get("text")
                                        elif isinstance(payload.get("result"), dict) and payload.get("result", {}).get("text"):
                                            text = payload.get("result", {}).get("text")
                                        elif payload.get("utterances") and len(payload.get("utterances", [])) > 0:
                                            utterance = payload.get("utterances")[0]
                                            if isinstance(utterance, dict) and utterance.get("text"):
                                                text = utterance.get("text")
                                        if text and isinstance(text, str) and text.strip():
                                            if is_last:
                                                transcript_text = text.strip()
                                                print(f"最终转录: {transcript_text}")
                                            # 中间结果不拼接，避免重复
                                    
                                    if is_last:
                                        return True  # 接收完成
                                
                                elif msg.type == aiohttp.WSMsgType.ERROR:
                                    print(f"WebSocket错误: {msg.data}")
                                    return False
                                elif msg.type == aiohttp.WSMsgType.CLOSE:
                                    print("WebSocket连接已关闭")
                                    return False
                            except asyncio.CancelledError:
                                return False
                    
                    # 并发执行发送和接收
                    send_task = asyncio.create_task(send_audio_segments())
                    recv_task = asyncio.create_task(receive_responses())
                    
                    try:
                        # 等待接收任务完成（发送任务会在后台完成）
                        await recv_task
                    finally:
                        # 取消发送任务（如果还在运行）
                        if not send_task.done():
                            send_task.cancel()
                            try:
                                await send_task
                            except asyncio.CancelledError:
                                pass
                    
                    if transcript_text and transcript_text.strip():
                        return transcript_text.strip()
                    else:
                        print("警告: 未提取到任何文本")
                        print("可能原因:")
                        print("1. 录音内容无法识别（静音、噪音或音量太小）")
                        print("2. 需要等待更长时间才能收到完整结果")
                        print("3. 响应格式可能不正确")
                        return None
                    
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"ASR WebSocket连接失败:\n{error_trace}")
            # 重新抛出异常，让上层可以捕获
            raise Exception(f"ASR WebSocket连接失败: {str(e)}") from e
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        语音转文字（同步包装器）
        
        Args:
            audio_data: WAV格式的音频数据
        
        Returns:
            转录文本
        """
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._transcribe_async(audio_data))
            except RuntimeError as e:
                if "This event loop is already running" in str(e) or "cannot be called from a running event loop" in str(e):
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(self._transcribe_async(audio_data))
                        )
                        return future.result(timeout=30)
                else:
                    raise
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"ASR transcribe错误:\n{error_trace}")
            # 重新抛出异常，让Flask可以捕获并返回错误信息
            raise Exception(f"ASR转录失败: {str(e)}") from e


class DoubaoTTSClient:
    """豆包TTS客户端（火山引擎 - WebSocket）"""
    
    def __init__(self, app_id: str = None, access_token: str = None, 
                 endpoint: str = None, voice_type: str = None, encoding: str = None):
        self.app_id = app_id or VOLCENGINE_APP_ID
        self.access_token = access_token or VOLCENGINE_ACCESS_TOKEN
        self.endpoint = endpoint or TTS_ENDPOINT
        self.voice_type = voice_type or TTS_VOICE_TYPE
        self.encoding = encoding or TTS_ENCODING
        
        if not self.app_id or not self.access_token:
            raise ValueError("请设置VOLCENGINE_APP_ID和VOLCENGINE_ACCESS_TOKEN环境变量")
    
    def _get_cluster(self, voice: str) -> str:
        """根据音色类型确定cluster"""
        if voice.startswith("S_"):
            return "volcano_icl"
        return "volcano_tts"
    
    async def _synthesize_async(self, text: str, voice_type: str = None, encoding: str = None) -> Optional[bytes]:
        """
        文字转语音（异步WebSocket实现）
        
        Args:
            text: 要合成的文本
            voice_type: 音色类型（可选，默认使用配置）
            encoding: 编码格式（可选，默认使用配置）
        
        Returns:
            音频数据（bytes）
        """
        if not text or not text.strip():
            return None
        
        voice_type = voice_type or self.voice_type
        encoding = encoding or self.encoding
        cluster = self._get_cluster(voice_type)
        
        # 导入protocols模块
        try:
            from .protocols import MsgType, full_client_request, receive_message
        except ImportError:
            print("错误: 无法导入protocols模块，请确保protocols目录存在")
            return None
        
        # 连接WebSocket
        headers = {
            "Authorization": f"Bearer;{self.access_token}",
        }
        
        try:
            # 豆包 TTS 服务建连可能较慢，延长连接超时时间
            websocket = await websockets.connect(
                self.endpoint,
                additional_headers=headers,
                max_size=10 * 1024 * 1024,
                open_timeout=60,
                close_timeout=10
            )
            
            try:
                # 构建请求
                request = {
                    "app": {
                        "appid": self.app_id,
                        "token": self.access_token,
                        "cluster": cluster,
                    },
                    "user": {
                        "uid": str(uuid.uuid4()),
                    },
                    "audio": {
                        "voice_type": voice_type,
                        "encoding": encoding,
                    },
                    "request": {
                        "reqid": str(uuid.uuid4()),
                        "text": text,
                        "operation": "submit",  # 关键：必须包含operation字段
                        "with_timestamp": "1",
                        "extra_param": json.dumps({
                            "disable_markdown_filter": False,
                        }),
                    },
                }
                
                # 发送请求
                await full_client_request(websocket, json.dumps(request).encode())
                
                # 接收音频数据
                audio_data = bytearray()
                while True:
                    msg = await receive_message(websocket)
                    
                    if msg.type == MsgType.FrontEndResultServer:
                        continue
                    elif msg.type == MsgType.AudioOnlyServer:
                        audio_data.extend(msg.payload)
                        if msg.sequence < 0:  # 最后一条消息
                            break
                    elif msg.type == MsgType.Error:
                        error_msg = msg.payload.decode('utf-8', errors='ignore') if msg.payload else "未知错误"
                        print(f"TTS API错误: {error_msg}, 错误码: {msg.error_code}")
                        return None
                    else:
                        print(f"TTS收到未知消息类型: {msg.type}, 消息: {msg}")
                        # 继续接收，可能还有音频数据
                        continue
                
                # 检查是否收到音频数据
                if not audio_data:
                    print("未收到音频数据")
                    return None
                
                return bytes(audio_data)
                
            finally:
                await websocket.close()
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"TTS WebSocket连接失败:\n{error_trace}")
            return None
    
    def synthesize(self, text: str, voice_type: str = None, encoding: str = None) -> Optional[bytes]:
        """
        文字转语音（同步包装器）
        
        Args:
            text: 要合成的文本
            voice_type: 音色类型（可选）
            encoding: 编码格式（可选）
        
        Returns:
            音频数据（bytes）
        """
        try:
            # 尝试获取现有的事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                # 如果没有事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 如果事件循环正在运行（比如在Flask中），需要使用nest_asyncio
            # 或者使用线程来运行异步代码
            try:
                return loop.run_until_complete(self._synthesize_async(text, voice_type, encoding))
            except RuntimeError as e:
                if "This event loop is already running" in str(e):
                    # 在已有事件循环中运行，需要使用线程
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(self._synthesize_async(text, voice_type, encoding))
                        )
                        return future.result(timeout=30)
                else:
                    raise
        except Exception as e:
            import traceback
            print(f"TTS synthesize错误:\n{traceback.format_exc()}")
            return None
