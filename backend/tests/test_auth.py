"""
인증 엔드포인트를 위한 테스트 케이스입니다.
"""

import pytest
from fastapi.testclient import TestClient


def test_user_signup(client: TestClient, db):
    """사용자 회원가입을 테스트합니다."""
    user_data = {
        "email": "newuser@example.com",
        "password": "StrongPass123!"
    }
    
    response = client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["success"] is True
    assert "User account created successfully" in data["message"]
    assert data["data"]["email"] == user_data["email"]


def test_user_login(client: TestClient, db):
    """사용자 로그인을 테스트합니다."""
    # 먼저 사용자 생성
    user_data = {
        "email": "login@example.com", 
        "password": "TestPass123!"
    }
    client.post("/api/v1/auth/signup", json=user_data)
    
    # 그 다음 로그인
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client: TestClient, auth_headers, db):
    """현재 사용자 프로필 조회를 테스트합니다."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert data["email"] == "test@example.com"


def test_invalid_login(client: TestClient, db):
    """잘못된 자격 증명으로 로그인을 테스트합니다."""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
