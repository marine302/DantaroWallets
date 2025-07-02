# USDT TRC20 지갑 서비스

거래소형 아키텍처를 기반으로 한 USDT (TRC20) 지갑 관리를 위한 FastAPI 백엔드 서비스입니다.

## 🌟 주요 기능

- **사용자 관리**: 회원가입, JWT 인증
- **잔액 관리**: USDT와 TRX의 실시간 잔액 추적
- **내부 이체**: 사용자 간 즉시, 무수수료 이체
- **입금 모니터링**: USDT 입금 자동 감지
- **출금 처리**: 관리자 승인 후 블록체인 실행
- **관리자 기능**: 사용자 관리, 출금 승인, 시스템 모니터링
- **관리자 웹 인터페이스**: 브라우저 기반 관리 대시보드

## 🏗️ 아키텍처

### 거래소 모델
- 모든 사용자 자산은 회사 지갑에서 중앙 관리
- 개별 사용자 잔액은 데이터베이스에서 추적
- 내부 이체는 즉시 데이터베이스 작업
- 외부 입출금은 블록체인과 상호작용

### 보안
- JWT 기반 인증
- 민감한 작업을 위한 관리자 전용 엔드포인트
- 출금 승인 워크플로우
- bcrypt 패스워드 해싱
- 트랜잭션 로깅 및 감사 추적

## 🚀 빠른 시작

### 필수 요구사항
- Python 3.10+
- PostgreSQL
- 회사 운영용 Tron 지갑

### 설치

1. **프로젝트 클론 및 이동:**
   ```bash
   cd backend
   ```

2. **설치 스크립트 실행:**
   ```bash
   ./setup.sh
   ```

3. **환경 설정:**
   `.env` 파일을 편집하여 설정:
   ```env
   DATABASE_URL="postgresql://user:password@localhost:5432/usdt_wallet"
   SECRET_KEY="your-super-secret-key-change-in-production"
   COMPANY_WALLET_ADDRESS="TYourCompanyWalletAddressHere"
   COMPANY_WALLET_PRIVATE_KEY="your-private-key"
   TRON_NETWORK="testnet"  # 또는 "mainnet"
   ```

4. **서버 시작:**
   ```bash
   python -m app.main
   ```

5. **API 문서 확인:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📚 API 엔드포인트

### 인증 (`/api/v1/auth`)
- `POST /signup` - 사용자 회원가입
- `POST /login` - 사용자 로그인
- `GET /me` - 현재 사용자 프로필 조회

### 지갑 (`/api/v1/wallet`)
- `GET /balance` - 사용자 잔액 조회
- `POST /transfer` - 내부 이체
- `GET /deposit/address` - 입금 주소 조회
- `POST /deposit/check` - 입금 확인

### 트랜잭션 (`/api/v1/transactions`)
- `GET /transactions` - 트랜잭션 내역
- `GET /transactions/{id}` - 트랜잭션 상세 정보
- `POST /withdraw` - 출금 요청 생성
- `GET /status/{tx_hash}` - 블록체인 트랜잭션 상태 확인

### 관리자 (`/api/v1/admin`)
- `GET /users` - 전체 사용자 목록
- `GET /balances` - 전체 잔액 조회
- `GET /withdrawals/pending` - 대기 중인 출금 요청
- `POST /withdrawals/approve` - 출금 승인/거부
- `POST /send` - 관리자 블록체인 트랜잭션
- `GET /system/status` - 시스템 상태

## 🖥️ 관리자 웹 인터페이스

브라우저 기반 관리 대시보드로 관리자가 직관적으로 시스템을 관리할 수 있습니다.

### 접속 방법
1. 서버 실행 후 `http://localhost:8000/admin` 접속
2. 관리자 계정으로 로그인

### 주요 기능
- **대시보드**: 실시간 통계, 시스템 상태, 최근 거래 내역
- **사용자 관리**: 사용자 목록, 상태 변경, 상세 정보 조회
- **출금 승인**: 대기 중인 출금 요청 검토 및 승인/거부
- **시스템 모니터링**: 서버 상태, 네트워크 정보, 버전 정보

### 페이지 구성
- `/admin` - 로그인 페이지
- `/admin/dashboard` - 관리자 대시보드
- `/admin/users` - 사용자 관리
- `/admin/withdrawals` - 출금 승인 관리

### 기술 스택
- **백엔드**: FastAPI + Jinja2 템플릿
- **프론트엔드**: Bootstrap 5 + jQuery + FontAwesome
- **인증**: 쿠키 기반 세션 관리
- **스타일링**: 커스텀 CSS + 반응형 디자인

### 보안 기능
- JWT 토큰 기반 인증
- 관리자 권한 검증
- 세션 자동 만료
- 브루트 포스 방지

## 🔧 개발

### 프로젝트 구조
```
backend/
├── app/
│   ├── main.py              # FastAPI 애플리케이션
│   ├── models.py            # SQLAlchemy 모델
│   ├── schemas.py           # Pydantic 스키마
│   ├── crud.py              # 데이터베이스 작업
│   ├── deps.py              # 의존성 주입
│   ├── core/
│   │   ├── config.py        # 설정
│   │   └── db.py            # 데이터베이스 설정
│   ├── routers/
│   │   ├── users.py         # 사용자 라우터
│   │   ├── wallet.py        # 지갑 라우터
│   │   ├── tx.py            # 트랜잭션 라우터
│   │   └── admin.py         # 관리자 라우터
│   └── utils/
│       ├── security.py      # 보안 유틸리티
│       └── tron.py          # Tron 블록체인 연동
├── tests/                   # 테스트 케이스
├── alembic/                 # 데이터베이스 마이그레이션
├── requirements.txt         # 의존성
├── .env.example             # 환경 변수 템플릿
└── setup.sh                 # 설치 스크립트
```

### 테스트 실행
```bash
# 가상환경 활성화
source venv/bin/activate

# 테스트 실행
pytest

# 커버리지와 함께 실행
pytest --cov=app tests/
```

### 데이터베이스 마이그레이션
```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "설명"

# 마이그레이션 적용
alembic upgrade head

# 다운그레이드
alembic downgrade -1
```

## 🔐 보안 고려사항

### 프로덕션 배포
1. 기본 관리자 자격증명 변경
2. 강력한 시크릿 키 사용 (최소 32자)
3. 적절한 CORS 출처 설정
4. 프로덕션에서 HTTPS 사용
5. 데이터베이스 연결 보안
6. 개인키 안전 저장 (하드웨어 지갑 고려)
7. 정기적인 보안 감사

### 환경 변수
- `.env` 파일을 버전 관리에 커밋하지 마세요
- 환경별 설정 사용
- 시크릿 정기적 순환

## 📊 모니터링

### 헬스 체크
- `GET /health` - 기본 헬스 체크
- `GET /api/v1/status` - 상세한 API 상태

### 로깅
- 요청/응답 로깅
- 에러 추적
- 성능 모니터링
- 관리자 작업 감사 추적

## 🛠️ 커스터마이징

### 새 자산 추가
1. 새 자산 유형을 지원하도록 모델 업데이트
2. 자산별 블록체인 연동 구현
3. 새 자산 주소 검증 추가
4. 관리자 인터페이스 업데이트

### 사용자 정의 비즈니스 로직
- `config.py`에서 트랜잭션 수수료 수정
- 사용자 정의 출금 한도 구현
- 추가 검증 규칙 추가
- 사용자 정의 관리자 승인 워크플로우

## 🐛 문제 해결

### 일반적인 문제

1. **데이터베이스 연결 실패**
   - PostgreSQL이 실행 중인지 확인
   - .env의 DATABASE_URL 확인
   - 데이터베이스가 존재하는지 확인

2. **Tron 트랜잭션 실패**
   - TRON_NETWORK 설정 확인
   - 회사 지갑에 수수료용 TRX가 있는지 확인
   - 개인키 형식 검증

3. **인증 문제**
   - SECRET_KEY 길이 확인 (최소 32자)
   - 토큰 만료 설정 확인
   - 오래된 토큰 삭제

### 디버그 모드
상세한 로깅 활성화:
```env
DEBUG=true
LOG_LEVEL="debug"
```

## 📄 라이선스

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 🤝 기여

1. 저장소를 포크하세요
2. 기능 브랜치를 생성하세요
3. 변경사항을 적용하세요
4. 테스트를 추가하세요
5. 풀 리퀘스트를 제출하세요

## 📞 지원

질문이나 문제가 있으시면:
- 저장소에서 이슈를 생성하세요
- `/docs`에서 API 문서를 확인하세요
- 위의 문제 해결 섹션을 검토하세요
