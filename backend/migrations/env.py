from logging.config import fileConfig
import os

from dotenv import load_dotenv
load_dotenv()  # .env 로드

from sqlalchemy import pool
from alembic import context

# our app’s MetaData and engine
from sqlmodel import SQLModel
from app.db import engine            # 실제 경로에 맞게 조정
from app.models import *             # SQLModel로 정의한 모델들이 있는 모듈

# Alembic Config 객체
config = context.config

# logging 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel metadata 지정 (autogenerate 사용)
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """오프라인 모드: URL만 이용해 SQL 스크립트 출력"""
    url = os.getenv(
        "DATABASE_URL",
        config.get_main_option("sqlalchemy.url")
    )
    config.set_main_option("sqlalchemy.url", url)
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드: 실제 DB에 연결해 마이그레이션 실행"""
    connectable = engine  # app.db 에서 만든 engine 사용

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
