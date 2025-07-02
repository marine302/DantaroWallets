"""
데이터베이스 마이그레이션을 위한 Alembic 설정입니다.
"""

from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Python 경로에 app 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.core.db import Base
from app import models  # 모든 모델 임포트

# Alembic 설정 객체
config = context.config

# SQLAlchemy URL 설정
config.set_main_option("sqlalchemy.url", settings.database_url)

# 대상 메타데이터
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드에서 마이그레이션을 실행합니다."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드에서 마이그레이션을 실행합니다."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

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
