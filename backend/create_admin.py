"""
초기 관리자 사용자 생성 스크립트.
시스템에서 첫 번째 관리자 사용자를 생성하기 위해 이 스크립트를 실행하세요.
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.db import SessionLocal, init_db
from app.crud import crud_user
from app.schemas import UserCreate
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user():
    """초기 관리자 사용자를 생성합니다."""
    logger.info("초기 관리자 사용자를 생성합니다...")
    
    # 데이터베이스 초기화
    init_db()
    
    db: Session = SessionLocal()
    try:
        # 관리자가 이미 존재하는지 확인
        existing_admin = crud_user.get_by_email(db, email=settings.admin_email)
        if existing_admin:
            logger.info(f"관리자 사용자가 이미 존재합니다: {settings.admin_email}")
            return
        
        # 관리자 사용자 생성
        admin_user_data = UserCreate(
            email=settings.admin_email,
            password=settings.admin_password
        )
        
        admin_user = crud_user.create(db, user_create=admin_user_data)
        
        # 사용자를 관리자로 설정
        from app.models import User
        db.query(User).filter(User.id == admin_user.id).update({"is_admin": True})
        db.commit()
        
        logger.info(f"✅ 관리자 사용자가 성공적으로 생성되었습니다: {settings.admin_email}")
        logger.info(f"🔐 기본 비밀번호: {settings.admin_password}")
        logger.info("⚠️  첫 로그인 후 기본 비밀번호를 변경해주세요!")
        
    except Exception as e:
        logger.error(f"❌ 관리자 사용자 생성 실패: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
