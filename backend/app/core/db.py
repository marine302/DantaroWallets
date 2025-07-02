"""
Database configuration and session management.
Handles SQLAlchemy setup for PostgreSQL connection.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .config import settings

# SQLAlchemy 엔진 생성
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # 개발환경에서 SQL 쿼리 로깅을 위해 True로 설정
)

# 데이터베이스 세션을 위한 SessionLocal 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모델 상속을 위한 Base 클래스 생성
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    This should be called once when setting up the application.
    """
    Base.metadata.create_all(bind=engine)
