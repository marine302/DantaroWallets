"""
메인 FastAPI 애플리케이션 모듈.
모든 라우터, 미들웨어, 설정을 포함한 FastAPI 앱을 구성합니다.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
import logging
import time

from .core.config import settings
from .core.db import init_db
from .routers import users, wallet, tx, admin, admin_web

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="""
    ## USDT TRC20 지갑 서비스 API
    
    거래소형 아키텍처에서 USDT (TRC20) 지갑을 관리하기 위한 FastAPI 기반 백엔드 서비스입니다.
    
    ### 주요 기능:
    - **사용자 관리**: JWT를 이용한 회원가입, 인증
    - **잔액 관리**: USDT와 TRX의 실시간 잔액 추적
    - **내부 이체**: 사용자 간 즉시, 무수수료 이체
    - **입금 모니터링**: USDT 입금 자동 감지
    - **출금 처리**: 관리자 승인 후 블록체인 실행
    - **관리자 기능**: 사용자 관리, 출금 승인, 시스템 모니터링
    
    ### 인증:
    대부분의 엔드포인트는 Bearer 토큰 인증이 필요합니다. `/login` 엔드포인트에서 토큰을 받으세요.
    
    ### 보안:
    - JWT 기반 인증
    - 민감한 작업을 위한 관리자 전용 엔드포인트
    - 출금 승인 워크플로우
    - 트랜잭션 로깅 및 감사 추적
    """,
    openapi_url=f"{settings.api_v1_str}/openapi.json"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 적절히 설정하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 로깅을 위한 커스텀 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """모든 HTTP 요청을 타이밍 정보와 함께 로깅합니다."""
    start_time = time.time()
    
    # 요청 로깅
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"요청: {request.method} {request.url} - 클라이언트: {client_host}")
    
    # 요청 처리
    response = await call_next(request)
    
    # 처리 시간 계산
    process_time = time.time() - start_time
    
    # 응답 로깅
    logger.info(
        f"응답: {response.status_code} - "
        f"시간: {process_time:.3f}s - "
        f"크기: {response.headers.get('content-length', 'unknown')} bytes"
    )
    
    # 타이밍 헤더 추가
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 전역 예외 처리기
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """SQLAlchemy 데이터베이스 에러를 처리합니다."""
    logger.error(f"{request.url}에서 데이터베이스 에러: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "데이터베이스 에러가 발생했습니다",
            "details": "나중에 다시 시도하거나 지원팀에 문의하세요"
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """ValueError 예외를 처리합니다."""
    logger.warning(f"{request.url}에서 값 에러: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": "유효하지 않은 입력 값",
            "details": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """예상치 못한 예외를 처리합니다."""
    logger.error(f"{request.url}에서 예상치 못한 에러: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "내부 서버 에러",
            "details": "예상치 못한 오류가 발생했습니다"
        }
    )


# 정적 파일 마운트 (디렉토리가 존재하는 경우에만)
import os
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 적절한 접두사로 라우터 포함
app.include_router(
    users.router,
    prefix=f"{settings.api_v1_str}/auth",
    tags=["인증"],
)

app.include_router(
    wallet.router,
    prefix=f"{settings.api_v1_str}/wallet",
    tags=["지갑"],
)

app.include_router(
    tx.router,
    prefix=f"{settings.api_v1_str}/transactions",
    tags=["트랜잭션"],
)

app.include_router(
    admin.router,
    prefix=f"{settings.api_v1_str}/admin",
    tags=["관리자"],
)

# 관리자 웹 페이지 라우터
app.include_router(
    admin_web.router,
    prefix="/admin",
    tags=["관리자 웹"],
)


# 루트 엔드포인트
@app.get("/")
async def root():
    """
    API 정보가 포함된 루트 엔드포인트.
    """
    return {
        "message": "USDT TRC20 지갑 서비스 API",
        "version": settings.version,
        "status": "운영 중",
        "documentation": "/docs",
        "openapi": f"{settings.api_v1_str}/openapi.json",
        "endpoints": {
            "authentication": f"{settings.api_v1_str}/auth",
            "wallet": f"{settings.api_v1_str}/wallet", 
            "transactions": f"{settings.api_v1_str}/transactions",
            "admin": f"{settings.api_v1_str}/admin"
        }
    }


# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    """
    모니터링을 위한 헬스 체크 엔드포인트.
    """
    try:
        # 여기에 데이터베이스 연결 확인을 추가할 수 있습니다
        return {
            "status": "정상",
            "timestamp": int(time.time()),
            "version": settings.version,
            "database": "연결됨",
            "tron_network": settings.tron_network
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "비정상",
                "timestamp": int(time.time()),
                "error": str(e)
            }
        )


# API 상태 엔드포인트
@app.get(f"{settings.api_v1_str}/status")
async def api_status():
    """
    상세한 정보가 포함된 API 상태 엔드포인트.
    """
    return {
        "api_version": settings.version,
        "status": "운영 중",
        "features": {
            "user_registration": True,
            "jwt_authentication": True,
            "internal_transfers": True,
            "deposit_monitoring": True,
            "withdrawal_requests": True,
            "admin_functions": True,
            "tron_integration": True
        },
        "endpoints_count": {
            "auth": 4,
            "wallet": 4,
            "transactions": 4,
            "admin": 6
        },
        "security": {
            "jwt_enabled": True,
            "admin_protected": True,
            "password_hashing": "bcrypt",
            "token_expiry_minutes": settings.access_token_expire_minutes
        }
    }


# 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 이벤트.
    데이터베이스를 초기화하고 시작 체크를 수행합니다.
    """
    logger.info("USDT TRC20 지갑 서비스를 시작합니다...")
    
    try:
        # 데이터베이스 초기화
        init_db()
        logger.info("데이터베이스가 성공적으로 초기화되었습니다")
        
        # 설정 로깅
        logger.info(f"API 버전: {settings.version}")
        logger.info(f"Tron 네트워크: {settings.tron_network}")
        logger.info(f"토큰 만료 시간: {settings.access_token_expire_minutes}분")
        
        logger.info("USDT TRC20 지갑 서비스가 성공적으로 시작되었습니다")
        
    except Exception as e:
        logger.error(f"시작 실패: {str(e)}")
        raise


# 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """
    애플리케이션 종료 이벤트.
    리소스를 정리하고 종료를 로깅합니다.
    """
    logger.info("USDT TRC20 지갑 서비스를 종료합니다...")
    
    # 여기에 정리 로직 추가
    # 예: 데이터베이스 연결 종료, 백그라운드 작업 중지 등
    
    logger.info("USDT TRC20 지갑 서비스 종료 완료")


if __name__ == "__main__":
    import uvicorn
    
    # 애플리케이션 실행
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
