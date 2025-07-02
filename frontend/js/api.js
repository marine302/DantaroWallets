/**
 * USDT 지갑 API 통신 모듈
 * FastAPI 백엔드와의 모든 API 통신을 관리합니다.
 */

class WalletAPI {
    constructor() {
        this.baseURL = 'http://localhost:8000/api/v1';
        this.token = localStorage.getItem('accessToken');
    }

    /**
     * HTTP 요청을 보내는 기본 메서드
     * @param {string} endpoint - API 엔드포인트
     * @param {Object} options - fetch 옵션
     * @returns {Promise<Object>} - API 응답
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // 인증 토큰 추가 (로그인/회원가입 제외)
        if (this.token && !endpoint.includes('/auth/')) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            console.log(`🌐 API 요청: ${config.method || 'GET'} ${url}`);
            const response = await fetch(url, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    // 토큰 만료 시 로그아웃 처리
                    this.logout();
                    throw new Error('세션이 만료되었습니다. 다시 로그인해주세요.');
                }
                
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log(`✅ API 응답: ${response.status}`, data);
            return data;
        } catch (error) {
            console.error(`❌ API 오류: ${config.method || 'GET'} ${url}`, error);
            throw error;
        }
    }

    /**
     * GET 요청
     */
    async get(endpoint, params = {}) {
        const searchParams = new URLSearchParams(params);
        const url = searchParams.toString() ? `${endpoint}?${searchParams}` : endpoint;
        return this.request(url);
    }

    /**
     * POST 요청
     */
    async post(endpoint, data = {}, contentType = 'application/json') {
        const options = {
            method: 'POST',
            headers: {}
        };

        if (contentType === 'application/json') {
            options.body = JSON.stringify(data);
            options.headers['Content-Type'] = 'application/json';
        } else if (contentType === 'application/x-www-form-urlencoded') {
            options.body = new URLSearchParams(data);
            options.headers['Content-Type'] = 'application/x-www-form-urlencoded';
        }

        return this.request(endpoint, options);
    }

    /**
     * PUT 요청
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE 요청
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    // ===== 인증 관련 API =====

    /**
     * 회원가입
     * @param {string} email - 이메일
     * @param {string} password - 비밀번호
     */
    async signup(email, password) {
        const response = await this.post('/auth/signup', { email, password });
        return response;
    }

    /**
     * 로그인
     * @param {string} email - 이메일
     * @param {string} password - 비밀번호
     */
    async login(email, password) {
        const response = await this.post('/auth/login', {
            username: email,
            password: password
        }, 'application/x-www-form-urlencoded');
        
        if (response.access_token) {
            this.token = response.access_token;
            localStorage.setItem('accessToken', this.token);
            localStorage.setItem('userEmail', email);
        }
        
        return response;
    }

    /**
     * 로그아웃
     */
    logout() {
        this.token = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('userEmail');
        window.location.href = '/';
    }

    /**
     * 현재 사용자 정보 조회
     */
    async getCurrentUser() {
        return this.get('/auth/me');
    }

    // ===== 지갑 관련 API =====

    /**
     * 잔액 조회
     * @param {string} asset - 자산 (선택적)
     */
    async getBalance(asset = null) {
        const params = asset ? { asset } : {};
        return this.get('/wallet/balance', params);
    }

    /**
     * 내부 이체
     * @param {string} toEmail - 받는 사람 이메일
     * @param {number} amount - 금액
     * @param {string} asset - 자산 (기본: USDT)
     * @param {string} memo - 메모 (선택적)
     */
    async transfer(toEmail, amount, asset = 'USDT', memo = '') {
        return this.post('/wallet/transfer', {
            to_email: toEmail,
            amount: parseFloat(amount),
            asset,
            memo
        });
    }

    /**
     * 출금 신청
     * @param {string} address - 출금 주소
     * @param {number} amount - 금액
     * @param {string} asset - 자산 (기본: USDT)
     * @param {string} memo - 메모 (선택적)
     */
    async withdraw(address, amount, asset = 'USDT', memo = '') {
        return this.post('/transactions/withdraw', {
            destination_address: address,
            amount: parseFloat(amount),
            asset,
            memo
        });
    }

    /**
     * 입금 주소 생성/조회
     * @param {string} asset - 자산 (기본: USDT)
     */
    async getDepositAddress(asset = 'USDT') {
        return this.get('/wallet/deposit/address');
    }

    // ===== 거래 내역 관련 API =====

    /**
     * 거래 내역 조회
     * @param {Object} params - 쿼리 매개변수
     */
    async getTransactions(params = {}) {
        const defaultParams = {
            skip: 0,
            limit: 20,
            ...params
        };
        return this.get('/transactions/transactions', defaultParams);
    }

    /**
     * 특정 거래 조회
     * @param {number} transactionId - 거래 ID
     */
    async getTransaction(transactionId) {
        return this.get(`/transactions/transactions/${transactionId}`);
    }

    // ===== 유틸리티 메서드 =====

    /**
     * 로그인 상태 확인
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * 저장된 사용자 이메일 반환
     */
    getUserEmail() {
        return localStorage.getItem('userEmail');
    }

    /**
     * 금액 포맷팅
     * @param {number} amount - 금액
     * @param {number} decimals - 소수점 자리수 (기본: 8)
     */
    formatAmount(amount, decimals = 8) {
        return parseFloat(amount).toFixed(decimals);
    }

    /**
     * 날짜 포맷팅
     * @param {string} dateString - 날짜 문자열
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * 거래 상태 한글 변환
     * @param {string} status - 거래 상태
     */
    getStatusText(status) {
        const statusMap = {
            'pending': '대기',
            'completed': '완료',
            'failed': '실패',
            'cancelled': '취소'
        };
        return statusMap[status] || status;
    }

    /**
     * 거래 유형 한글 변환
     * @param {string} type - 거래 유형
     */
    getTypeText(type) {
        const typeMap = {
            'deposit': '입금',
            'withdrawal': '출금',
            'transfer': '이체',
            'payment': '결제'
        };
        return typeMap[type] || type;
    }
}

// 전역 API 인스턴스
window.walletAPI = new WalletAPI();
