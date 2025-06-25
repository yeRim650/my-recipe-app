# 베이스 이미지
FROM python:3.10-slim

# 작업 디렉토리 생성
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-dotenv \
    sqlmodel \
    pymysql \
    cryptography \
    qdrant-client \
    sentence-transformers \
    alembic \
    openai

# 소스 코드 복사
COPY ./app ./app
COPY ./migrations ./migrations
COPY ./alembic.ini ./alembic.ini
COPY ./recipe_rag_pipeline.py ./recipe_rag_pipeline.py
COPY ./seed_data.py ./seed_data.py
COPY ./delete_and_recreate.py ./delete_and_recreate.py
COPY ./init_data.py ./init_data.py

# 포트 오픈
EXPOSE 8000

# FastAPI 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 