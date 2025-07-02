"""
USDT TRC20 월렛 서비스의 핵심 설정 모듈입니다.
환경 변수와 애플리케이션 설정을 관리합니다.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """환경 변수를 지원하는 애플리케이션 설정 클래스입니다."""
    
    # API 설정
    project_name: str = "USDT TRC20 Wallet Service"
    version: str = "1.0.0"
    api_v1_str: str = "/api/v1"
    
    # 보안 설정
    secret_key: str = "your-super-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # 데이터베이스 설정
    database_url: str = "postgresql://user:password@localhost:5432/usdt_wallet"
    
    # 트론 네트워크 설정
    tron_api_key: Optional[str] = None
    tron_network: str = "mainnet"  # 메인넷 또는 테스트넷
    company_wallet_address: str = ""
    company_wallet_private_key: str = ""  # 보안 유지 필수!
    
    # 관리자 설정
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"  # 운영환경에서 변경 필요
    
    # 운영 설정
    min_withdrawal_amount: float = 10.0
    max_withdrawal_amount: float = 10000.0
    withdrawal_fee_percentage: float = 0.005  # 0.5%
    
    # 디버그 설정
    debug: bool = False
    log_level: str = "info"
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()
