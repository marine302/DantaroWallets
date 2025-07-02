"""
테스트 설정 및 픽스처 모듈입니다.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db, Base
from app.core.config import settings

# 테스트 데이터베이스 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """테스트용 데이터베이스 의존성을 오버라이드합니다."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db():
    """테스트 데이터베이스를 생성합니다."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """테스트 클라이언트를 생성합니다."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client, db):
    """인증된 사용자를 생성하고 인증 헤더를 반환합니다."""
    # 테스트 사용자 생성
    user_data = {
        "email": "test@example.com",
        "password": "Test123456!"
    }
    
    # 사용자 등록
    response = client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 201
    
    # 로그인하고 토큰 얻기
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
