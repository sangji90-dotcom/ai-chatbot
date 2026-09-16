FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 비루트 실행
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

ENV DB_PATH=/data/chatbot.db \
    UPLOAD_DIR=/data/images \
    RUN_SCHEDULER=0

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -fsS http://localhost:8000/health || exit 1

# 워커를 늘려도 스케줄러는 전용 컨테이너에서만 돈다 (compose 의 scheduler 서비스)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
