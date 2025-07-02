/**
 * 인증 관리 모듈
 * 로그인, 회원가입, 세션 관리를 담당합니다.
 */

class AuthManager {
    constructor() {
        this.init();
    }

    /**
     * 초기화
     */
    init() {
        // 페이지 로드 시 인증 상태 확인
        this.checkAuthStatus();
        
        // 폼 이벤트 리스너 등록
        this.setupEventListeners();
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 로그인 폼
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // 회원가입 폼
        const signupForm = document.getElementById('signupForm');
        if (signupForm) {
            signupForm.addEventListener('submit', (e) => this.handleSignup(e));
        }

        // 로그아웃 버튼
        const logoutBtns = document.querySelectorAll('.logout-btn');
        logoutBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleLogout(e));
        });

        // 인증 모드 전환 (로그인 ↔ 회원가입)
        const authToggleBtns = document.querySelectorAll('.auth-toggle-btn');
        authToggleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.toggleAuthMode(e));
        });
    }

    /**
     * 인증 상태 확인
     */
    checkAuthStatus() {
        const isAuthenticated = walletAPI.isAuthenticated();
        const currentPath = window.location.pathname;

        if (isAuthenticated) {
            // 로그인된 상태에서 로그인 페이지 접근 시 대시보드로 리다이렉트
            if (currentPath === '/' || currentPath === '/index.html') {
                window.location.href = '/dashboard.html';
                return;
            }
            
            // 사용자 정보 표시
            this.displayUserInfo();
        } else {
            // 로그인되지 않은 상태에서 보호된 페이지 접근 시 로그인 페이지로 리다이렉트
            const protectedPages = ['/dashboard.html', '/wallet.html', '/history.html'];
            if (protectedPages.includes(currentPath)) {
                window.location.href = '/';
                return;
            }
        }
    }

    /**
     * 사용자 정보 표시
     */
    async displayUserInfo() {
        try {
            const userEmail = walletAPI.getUserEmail();
            const userEmailElements = document.querySelectorAll('.user-email');
            userEmailElements.forEach(element => {
                element.textContent = userEmail;
            });
        } catch (error) {
            console.error('사용자 정보 표시 오류:', error);
        }
    }

    /**
     * 로그인 처리
     */
    async handleLogin(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const email = formData.get('email');
        const password = formData.get('password');

        // 폼 비활성화
        this.setFormLoading(form, true);
        
        try {
            const response = await walletAPI.login(email, password);
            
            // 성공 메시지
            this.showAlert('success', '로그인에 성공했습니다!');
            
            // 대시보드로 리다이렉트
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 1000);
            
        } catch (error) {
            this.showAlert('danger', error.message || '로그인에 실패했습니다.');
        } finally {
            this.setFormLoading(form, false);
        }
    }

    /**
     * 회원가입 처리
     */
    async handleSignup(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const email = formData.get('email');
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');

        // 비밀번호 확인
        if (password !== confirmPassword) {
            this.showAlert('danger', '비밀번호가 일치하지 않습니다.');
            return;
        }

        // 비밀번호 강도 검사
        if (!this.validatePassword(password)) {
            this.showAlert('danger', '비밀번호는 8자 이상이며 영문, 숫자, 특수문자를 포함해야 합니다.');
            return;
        }

        // 폼 비활성화
        this.setFormLoading(form, true);
        
        try {
            const response = await walletAPI.signup(email, password);
            
            // 성공 메시지
            this.showAlert('success', '회원가입에 성공했습니다! 로그인 페이지로 이동합니다.');
            
            // 로그인 페이지로 리다이렉트
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
            
        } catch (error) {
            this.showAlert('danger', error.message || '회원가입에 실패했습니다.');
        } finally {
            this.setFormLoading(form, false);
        }
    }

    /**
     * 로그아웃 처리
     */
    handleLogout(event) {
        event.preventDefault();
        
        if (confirm('정말 로그아웃하시겠습니까?')) {
            walletAPI.logout();
        }
    }

    /**
     * 인증 모드 전환 (로그인 ↔ 회원가입)
     */
    toggleAuthMode(event) {
        event.preventDefault();
        
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');
        
        if (loginForm && signupForm) {
            loginForm.classList.toggle('hidden');
            signupForm.classList.toggle('hidden');
        }
    }

    /**
     * 로그인 폼 표시
     */
    showLoginForm() {
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');
        
        if (loginForm && signupForm) {
            loginForm.classList.remove('hidden');
            signupForm.classList.add('hidden');
        }
    }

    /**
     * 회원가입 폼 표시
     */
    showSignupForm() {
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');
        
        if (loginForm && signupForm) {
            loginForm.classList.add('hidden');
            signupForm.classList.remove('hidden');
        }
    }

    /**
     * 폼 로딩 상태 설정
     */
    setFormLoading(form, isLoading) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const inputs = form.querySelectorAll('input');
        
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="spinner"></div> 처리 중...';
            inputs.forEach(input => input.disabled = true);
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = submitBtn.dataset.originalText || '로그인';
            inputs.forEach(input => input.disabled = false);
        }
    }

    /**
     * 비밀번호 유효성 검사
     */
    validatePassword(password) {
        // 최소 8자, 영문, 숫자, 특수문자 포함
        const regex = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
        return regex.test(password);
    }

    /**
     * 이메일 유효성 검사
     */
    validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    /**
     * 알림 메시지 표시
     */
    showAlert(type, message) {
        // 기존 알림 제거
        const existingAlert = document.querySelector('.alert');
        if (existingAlert) {
            existingAlert.remove();
        }

        // 새 알림 생성
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        // 폼 위에 삽입
        const form = document.querySelector('form');
        if (form) {
            form.parentNode.insertBefore(alert, form);
        }

        // 자동 제거
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    /**
     * 페이지 리다이렉트 가드
     */
    requireAuth() {
        if (!walletAPI.isAuthenticated()) {
            window.location.href = '/';
            return false;
        }
        return true;
    }

    /**
     * 게스트 전용 페이지 가드
     */
    requireGuest() {
        if (walletAPI.isAuthenticated()) {
            window.location.href = '/dashboard.html';
            return false;
        }
        return true;
    }
}

// 전역 인스턴스 생성
window.authManager = new AuthManager();
