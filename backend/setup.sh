#!/bin/bash

# USDT TRC20 지갑 서비스 - 개발 환경 설정 스크립트

echo "🚀 USDT TRC20 지갑 서비스를 설정합니다..."

# Python 3.10+ 설치 여부 확인
python_version=$(python3 --version 2>&1 | cut -d" " -f2 | cut -d"." -f1-2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ 이상이 필요합니다. 현재 버전: $python_version"
    exit 1
fi

echo "✅ Python 버전: $python_version"

# 가상환경이 존재하지 않으면 생성
if [ ! -d "venv" ]; then
    echo "📦 가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔧 가상환경을 활성화합니다..."
source venv/bin/activate

# 의존성 설치
echo "📥 의존성을 설치합니다..."
pip install --upgrade pip
pip install -r requirements.txt

# .env 파일이 존재하지 않으면 생성
if [ ! -f ".env" ]; then
    echo "⚙️  .env 파일을 생성합니다..."
    cp .env.example .env
    echo "📝 .env 파일을 사용자 설정에 맞게 편집해주세요"
fi

# 데이터베이스 초기화 (필요시)
echo "🗄️  데이터베이스를 초기화합니다..."
if [ ! -d "alembic/versions" ]; then
    mkdir -p alembic/versions
fi

# 초기 마이그레이션 생성
echo "📝 데이터베이스 마이그레이션을 생성합니다..."
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 실행
echo "🔄 데이터베이스 마이그레이션을 실행합니다..."
alembic upgrade head

echo "✅ 설정 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 데이터베이스 및 Tron 설정으로 .env 파일 편집"
echo "2. 개발 서버 실행: python -m app.main"
echo "3. API 문서 확인: http://localhost:8000/docs"
echo ""
echo "🔐 기본 관리자 자격증명 (프로덕션에서 변경하세요):"
echo "   이메일: admin@example.com"
echo "   비밀번호: admin123"
