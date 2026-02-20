# 瘦身镜像：豆包/OpenAI 部署，无 PyTorch/CUDA
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 音频处理依赖：soundfile + ffmpeg（pydub 用 ffmpeg 将 webm 转为 wav，豆包 ASR 必须）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY data /app/data
COPY characters /app/characters
COPY .env.sample /app/.env.sample

RUN mkdir -p /app/outputs /app/memory

EXPOSE 8000
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
