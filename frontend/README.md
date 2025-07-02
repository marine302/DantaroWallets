# USDT 지갑 서비스 프론트엔드

이 프론트엔드는 FastAPI 백엔드와 통신하는 사용자 웹 인터페이스입니다.

## 📁 파일 구조

```
frontend/
├── index.html          # 로그인/회원가입 페이지
├── dashboard.html      # 대시보드
├── wallet.html         # 지갑 관리
├── history.html        # 거래 내역
├── css/
│   └── style.css       # 모든 스타일
└── js/
    ├── api.js          # API 통신
    ├── auth.js         # 인증 관리
    ├── wallet.js       # 지갑 기능
    └── main.js         # 공통 기능
```

## 🚀 사용법

### 개발 환경에서 실행

1. **백엔드 서버 실행**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
   ```

2. **프론트엔드 서버 실행**
   ```bash
   cd frontend
   # 간단한 HTTP 서버 (Python 3)
   python3 -m http.server 8000
   
   # 또는 Node.js http-server
   npx http-server -p 8000 -c-1
   
   # 또는 Live Server (VS Code 확장)
   ```

3. **브라우저에서 접속**
   - 프론트엔드: http://localhost:8000
   - 백엔드 API: http://localhost:8001

### 테스트 계정

개발 중에는 다음 계정을 사용할 수 있습니다:
- 이메일: `admin@example.com`
- 비밀번호: `admin123`

## 🔧 설정

### API 서버 주소 변경

`js/api.js` 파일에서 `baseURL`을 수정하세요:

```javascript
class WalletAPI {
    constructor() {
        this.baseURL = 'http://localhost:8001/api/v1'; // 여기를 수정
        this.token = localStorage.getItem('accessToken');
    }
}
```

## 📱 주요 기능

### 인증
- 회원가입 및 로그인
- JWT 토큰 기반 인증
- 자동 로그아웃 (토큰 만료 시)

### 대시보드
- 잔액 요약
- 빠른 액션 버튼
- 최근 거래 내역

### 지갑 관리
- USDT/TRX 잔액 조회
- 내부 이체 (사용자 간)
- USDT 입금/출금
- 주소 검증 도구

### 거래 내역
- 모든 거래 기록 조회
- 필터링 및 검색
- 페이지네이션
- 데이터 내보내기 (CSV, JSON)

## 🎨 UI/UX 특징

- **반응형 디자인**: 모바일과 데스크톱 지원
- **다크 모드**: 시스템 설정에 따라 자동 전환
- **실시간 알림**: 성공/오류 메시지
- **모달 인터페이스**: 깔끔한 사용자 경험
- **로딩 상태**: 비동기 작업 진행 표시

## 🔒 보안 고려사항

- XSS 방지를 위한 입력 검증
- CSRF 보호
- 민감한 정보 로컬 저장 금지
- HTTPS 사용 권장

## 🌐 브라우저 호환성

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 📦 의존성

외부 라이브러리:
- Font Awesome (아이콘)
- 기본 브라우저 API만 사용 (jQuery 없음)

## 🔧 커스터마이징

### 색상 테마 변경

`css/style.css`의 CSS 변수를 수정하세요:

```css
:root {
    --primary-color: #2563eb;    /* 메인 색상 */
    --success-color: #059669;    /* 성공 색상 */
    --warning-color: #d97706;    /* 경고 색상 */
    --danger-color: #dc2626;     /* 위험 색상 */
}
```

### 새로운 페이지 추가

1. HTML 파일 생성
2. 네비게이션 메뉴에 링크 추가
3. 필요한 JavaScript 함수 구현
4. CSS 스타일 추가

## 🐛 문제 해결

### 일반적인 문제들

1. **CORS 오류**
   - 백엔드에서 CORS 설정 확인
   - 개발 환경에서는 `--disable-web-security` 플래그 사용

2. **로그인 실패**
   - 백엔드 서버 실행 상태 확인
   - API 엔드포인트 URL 확인
   - 브라우저 개발자 도구에서 네트워크 탭 확인

3. **스타일 깨짐**
   - 브라우저 캐시 삭제
   - CSS 파일 경로 확인

## 📈 개발 가이드

### 새로운 API 추가

1. `js/api.js`에 API 메서드 추가
2. 해당 기능을 사용할 페이지에서 호출
3. 오류 처리 및 로딩 상태 관리

### 새로운 모달 추가

1. HTML에 모달 구조 추가
2. CSS에 필요한 스타일 추가
3. JavaScript에서 `showModal()`, `closeModal()` 함수 사용

## 📞 지원

문제가 발생하거나 문의사항이 있으면:
- GitHub Issues 생성
- 개발팀에 문의

---

**주의**: 이는 개발/테스트용 인터페이스입니다. 실제 운영 환경에서는 추가적인 보안 조치가 필요합니다.
