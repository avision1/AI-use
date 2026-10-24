FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/opt/huggingface
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
COPY amazing_tts/ ./amazing_tts/
# CPU-only PyTorch avoids multi-gigabyte CUDA dependencies.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu 'torch>=2.6,<3' && pip install --no-cache-dir '.[speech,cloud]'
# Bake voice/model assets and the English NLP model into the image once.
RUN python -m spacy download en_core_web_sm && python -m amazing_tts.preload
ENV AMAZING_TTS_CLOUD=1 HF_HUB_OFFLINE=1
CMD ["sh", "-c", "exec uvicorn amazing_tts.web:app --host 0.0.0.0 --port ${PORT:-8080}"]
