# 临时音频 token 存储，供豆包录音文件识别 API 通过 URL 拉取音频
import os
import time
import uuid

_audio_temp_store = {}
_audio_temp_ttl = 300


def register_audio_temp(file_path: str) -> str:
    """注册临时音频路径，返回 token。用于豆包录音文件识别 API 的 audio.url。"""
    token = uuid.uuid4().hex
    _audio_temp_store[token] = (file_path, time.time() + _audio_temp_ttl)
    return token


def get_audio_temp_path(token: str):
    """根据 token 取路径与是否过期。返回 (path, expired: bool)。"""
    if token not in _audio_temp_store:
        return None, True
    path, expiry = _audio_temp_store[token]
    expired = time.time() > expiry
    return path, expired


def unregister_audio_temp(token: str) -> None:
    """移除 token，转写完成后可调用以提前释放。"""
    _audio_temp_store.pop(token, None)
