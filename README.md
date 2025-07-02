# 🪙 DantaroWallets - USDT TRC20 지갑 시스템

완전한 USDT (TRC20) 지갑 관리 시스템으로, FastAPI 백엔드와 현대적인 웹 프론트엔드를 제공합니다.

## ✨ 주요 기능

### 🔐 사용자 기능
- **회원가입/로그인** - JWT 기반 보안 인증
- **지갑 관리** - USDT 및 TRX 잔액 실시간 조회
- **내부 이체** - 사용자 간 즉시, 무수수료 이체
- **입금/출금** - 블록체인 연동 입출금 처리
- **거래 내역** - 상세한 거래 기록 및 필터링

### 👨‍💼 관리자 기능
- **사용자 관리** - 계정 관리 및 모니터링
- **출금 승인** - 보안을 위한 수동 승인 프로세스
- **시스템 모니터링** - 실시간 시스템 상태 확인
- **웹 대시보드** - 브라우저 기반 관리 인터페이스

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   프론트엔드      │ ←→ │   FastAPI 백엔드  │ ←→ │   PostgreSQL    │
│   (HTML/CSS/JS) │    │   (Python 3.10+) │    │   데이터베이스    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              ↕
                       ┌─────────────────┐
                       │   Tron 블록체인   │
                       │   (TRC20 USDT)  │
                       └─────────────────┘
```

## 🚀 빠른 시작

### 필수 요구사항
- Python 3.10+
- PostgreSQL
- Node.js (선택사항)

### 백엔드 설정

```bash
# 1. 백엔드 디렉토리로 이동
cd backend

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 데이터베이스 및 Tron 설정 입력

# 5. 데이터베이스 초기화
alembic upgrade head

# 6. 관리자 계정 생성
python create_admin.py

# 7. 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 설정

```bash
# 1. 프론트엔드 디렉토리로 이동
cd frontend

# 2. 로컬 HTTP 서버 실행
python -m http.server 8080

# 또는 Node.js 사용
npx http-server -p 8080
```

## 🌐 접속 방법

- **사용자 웹 인터페이스**: http://localhost:8080
- **API 문서**: http://localhost:8000/docs
- **관리자 웹 패널**: http://localhost:8000/admin

### 데모 계정
- **이메일**: test@example.com
- **비밀번호**: Test123456

## 📁 프로젝트 구조

```
DantaroWallets/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── core/           # 핵심 설정 및 데이터베이스
│   │   ├── routers/        # API 라우터
│   │   ├── utils/          # 유틸리티 함수
│   │   ├── static/         # 정적 파일 (관리자 UI)
│   │   └── templates/      # HTML 템플릿
│   ├── alembic/            # 데이터베이스 마이그레이션
│   └── tests/              # 테스트 파일
│
└── frontend/               # 웹 프론트엔드
    ├── css/               # 스타일시트
    ├── js/                # JavaScript 모듈
    ├── login.html         # 로그인 페이지
    ├── signup.html        # 회원가입 페이지
    ├── dashboard.html     # 대시보드
    ├── wallet.html        # 지갑 관리
    └── history.html       # 거래 내역
```

## 🛠️ API 엔드포인트

### 인증
- `POST /api/v1/auth/signup` - 회원가입
- `POST /api/v1/auth/login` - 로그인

### 지갑
- `GET /api/v1/wallet/balance` - 잔액 조회
- `POST /api/v1/wallet/transfer` - 내부 이체
- `GET /api/v1/wallet/deposit/address` - 입금 주소 조회

### 거래
- `POST /api/v1/transactions/withdraw` - 출금 요청
- `GET /api/v1/transactions/transactions` - 거래 내역

### 관리자
- `GET /api/v1/admin/users` - 사용자 목록
- `POST /api/v1/admin/withdraw/{id}/approve` - 출금 승인

## 🎨 프론트엔드 특징

- **모던 디자인**: 현대적이고 직관적인 사용자 인터페이스
- **반응형**: 모바일과 데스크톱 모두 지원
- **한국어 지원**: 완전한 한국어 인터페이스
- **접근성**: 고대비 모드 및 키보드 탐색 지원
- **모듈식 구조**: 재사용 가능한 JavaScript 모듈

## 🔐 보안 기능

- **JWT 토큰**: 안전한 인증 및 세션 관리
- **비밀번호 해싱**: bcrypt를 이용한 강력한 암호화
- **출금 승인**: 관리자 수동 승인으로 보안 강화
- **CORS 설정**: 크로스 오리진 요청 보안
- **입력 검증**: 모든 사용자 입력에 대한 검증

## 📊 기술 스택

### 백엔드
- **FastAPI** - 고성능 Python 웹 프레임워크
- **SQLAlchemy** - ORM 및 데이터베이스 관리
- **PostgreSQL** - 메인 데이터베이스
- **Alembic** - 데이터베이스 마이그레이션
- **JWT** - 토큰 기반 인증
- **bcrypt** - 비밀번호 해싱

### 프론트엔드
- **HTML5/CSS3** - 마크업 및 스타일링
- **Vanilla JavaScript** - 클라이언트 로직
- **Font Awesome** - 아이콘
- **CSS Variables** - 테마 및 색상 관리

### 블록체인
- **Tron Network** - TRC20 USDT 지원
- **TronPy** - Python Tron 라이브러리

## 🤝 기여하기

1. 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🐛 버그 리포트 및 기능 요청

[Issues](https://github.com/marine302/DantaroWallets/issues) 페이지에서 버그 리포트나 기능 요청을 제출해주세요.

## 📞 지원

프로젝트에 대한 질문이나 지원이 필요한 경우:
- GitHub Issues 사용
- 프로젝트 Wiki 확인
- 코드 내 주석 및 문서 참조

---

⭐ 이 프로젝트가 유용하다면 스타를 눌러주세요!
