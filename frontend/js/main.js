/**
 * 메인 애플리케이션 모듈
 * 전체 앱의 초기화와 공통 기능을 담당합니다.
 */

class MainApp {
    constructor() {
        this.init();
    }

    /**
     * 애플리케이션 초기화
     */
    init() {
        // DOM 로드 완료 시 실행
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
    }

    /**
     * DOM 준비 완료 시 실행
     */
    onDOMReady() {
        this.setupGlobalEventListeners();
        this.initCurrentPage();
        this.setupNavigation();
        this.checkNetworkStatus();
    }

    /**
     * 전역 이벤트 리스너 설정
     */
    setupGlobalEventListeners() {
        // 전역 오류 처리
        window.addEventListener('error', (event) => {
            console.error('전역 오류:', event.error);
            this.showNotification('error', '예상치 못한 오류가 발생했습니다.');
        });

        // API 오류 처리
        window.addEventListener('unhandledrejection', (event) => {
            console.error('처리되지 않은 Promise 거부:', event.reason);
            if (event.reason?.message?.includes('401')) {
                this.showNotification('warning', '로그인이 필요합니다.');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            }
        });

        // 복사 버튼들
        const copyBtns = document.querySelectorAll('.copy-btn');
        copyBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleCopy(e));
        });

        // 새로고침 버튼들
        const refreshBtns = document.querySelectorAll('.refresh-btn');
        refreshBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleRefresh(e));
        });
    }

    /**
     * 현재 페이지 초기화
     */
    initCurrentPage() {
        const path = window.location.pathname;
        const page = this.getPageFromPath(path);

        switch (page) {
            case 'index':
                this.initIndexPage();
                break;
            case 'dashboard':
                this.initDashboardPage();
                break;
            case 'wallet':
                this.initWalletPage();
                break;
            case 'history':
                this.initHistoryPage();
                break;
        }
    }

    /**
     * 경로에서 페이지 이름 추출
     */
    getPageFromPath(path) {
        if (path === '/' || path === '/index.html' || path === '') {
            return 'index';
        }
        
        const pageName = path.replace('/', '').replace('.html', '');
        return pageName || 'index';
    }

    /**
     * 인덱스 페이지 초기화
     */
    initIndexPage() {
        // 이미 로그인된 사용자는 대시보드로 리다이렉트
        if (walletAPI.isAuthenticated()) {
            window.location.href = '/dashboard.html';
        }
    }

    /**
     * 대시보드 페이지 초기화
     */
    initDashboardPage() {
        if (!authManager.requireAuth()) return;

        // 대시보드 데이터 로드
        this.loadDashboardData();
        
        // 자동 새로고침 설정 (30초마다)
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }

    /**
     * 지갑 페이지 초기화
     */
    initWalletPage() {
        if (!authManager.requireAuth()) return;

        // 지갑 데이터 로드
        walletManager.loadBalance();
    }

    /**
     * 거래 내역 페이지 초기화
     */
    initHistoryPage() {
        if (!authManager.requireAuth()) return;

        // 거래 내역 로드
        this.loadTransactionHistory();
        
        // 필터 이벤트 리스너
        const filterForm = document.getElementById('filterForm');
        if (filterForm) {
            filterForm.addEventListener('submit', (e) => this.handleFilterTransactions(e));
        }

        // 페이지네이션 이벤트 리스너
        const paginationBtns = document.querySelectorAll('.pagination-btn');
        paginationBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handlePagination(e));
        });
    }

    /**
     * 네비게이션 설정
     */
    setupNavigation() {
        // 활성 메뉴 표시
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-item a');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath || 
                (currentPath === '/' && link.getAttribute('href') === '/dashboard.html')) {
                link.classList.add('active');
            }
        });

        // 모바일 메뉴 토글
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const navMenu = document.querySelector('.nav-menu');
        
        if (mobileMenuBtn && navMenu) {
            mobileMenuBtn.addEventListener('click', () => {
                navMenu.classList.toggle('show');
            });
        }
    }

    /**
     * 네트워크 상태 확인
     */
    checkNetworkStatus() {
        if (!navigator.onLine) {
            this.showNotification('warning', '인터넷 연결을 확인해주세요.');
        }

        window.addEventListener('online', () => {
            this.showNotification('success', '인터넷에 다시 연결되었습니다.');
        });

        window.addEventListener('offline', () => {
            this.showNotification('warning', '인터넷 연결이 끊어졌습니다.');
        });
    }

    /**
     * 대시보드 데이터 로드
     */
    async loadDashboardData() {
        try {
            // 잔액 로드
            if (window.walletManager) {
                await walletManager.loadBalance();
                await walletManager.loadDashboardStats();
            }
            
        } catch (error) {
            console.error('대시보드 데이터 로드 오류:', error);
        }
    }

    /**
     * 거래 내역 로드
     */
    async loadTransactionHistory(params = {}) {
        try {
            this.showLoading('history-loading', true);
            
            const defaultParams = {
                skip: 0,
                limit: 20,
                ...params
            };
            
            const response = await walletAPI.getTransactions(defaultParams);
            this.displayTransactionHistory(response.transactions || []);
            this.updatePagination(response.total || 0, defaultParams.skip, defaultParams.limit);
            
        } catch (error) {
            console.error('거래 내역 로드 오류:', error);
            this.showNotification('error', '거래 내역을 불러오는데 실패했습니다.');
        } finally {
            this.showLoading('history-loading', false);
        }
    }

    /**
     * 거래 내역 표시
     */
    displayTransactionHistory(transactions) {
        const tbody = document.getElementById('transactionTableBody');
        if (!tbody) return;

        if (transactions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">거래 내역이 없습니다.</td>
                </tr>
            `;
            return;
        }

        const html = transactions.map(tx => `
            <tr>
                <td>${walletAPI.formatDate(tx.created_at)}</td>
                <td>
                    <span class="badge badge-${this.getTypeBadgeClass(tx.type)}">
                        ${walletAPI.getTypeText(tx.type)}
                    </span>
                </td>
                <td class="text-right ${tx.type === 'withdrawal' ? 'text-danger' : 'text-success'}">
                    ${tx.type === 'withdrawal' ? '-' : '+'}${walletAPI.formatAmount(tx.amount)} ${tx.asset}
                </td>
                <td>
                    <span class="badge badge-${walletManager.getStatusBadgeClass(tx.status)}">
                        ${walletAPI.getStatusText(tx.status)}
                    </span>
                </td>
                <td class="text-right">
                    ${walletAPI.formatAmount(tx.fee_amount || 0)} ${tx.asset}
                </td>
                <td>
                    <small class="text-secondary">${this.truncateString(tx.memo || '-', 20)}</small>
                </td>
            </tr>
        `).join('');

        tbody.innerHTML = html;
    }

    /**
     * 거래 유형에 따른 배지 클래스
     */
    getTypeBadgeClass(type) {
        const classMap = {
            'deposit': 'success',
            'withdrawal': 'danger',
            'transfer': 'info',
            'payment': 'warning'
        };
        return classMap[type] || 'info';
    }

    /**
     * 페이지네이션 업데이트
     */
    updatePagination(total, skip, limit) {
        const paginationContainer = document.getElementById('pagination');
        if (!paginationContainer) return;

        const currentPage = Math.floor(skip / limit) + 1;
        const totalPages = Math.ceil(total / limit);

        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let html = '';
        
        // 이전 버튼
        if (currentPage > 1) {
            html += `<button class="btn btn-outline pagination-btn" data-page="${currentPage - 1}">이전</button>`;
        }

        // 페이지 번호들
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === currentPage ? 'btn-primary' : 'btn-outline';
            html += `<button class="btn ${isActive} pagination-btn" data-page="${i}">${i}</button>`;
        }

        // 다음 버튼
        if (currentPage < totalPages) {
            html += `<button class="btn btn-outline pagination-btn" data-page="${currentPage + 1}">다음</button>`;
        }

        paginationContainer.innerHTML = html;

        // 새로운 버튼들에 이벤트 리스너 추가
        const newBtns = paginationContainer.querySelectorAll('.pagination-btn');
        newBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handlePagination(e));
        });
    }

    /**
     * 필터 처리
     */
    handleFilterTransactions(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const params = {
            type: formData.get('type') || undefined,
            status: formData.get('status') || undefined,
            asset: formData.get('asset') || undefined,
            skip: 0 // 필터 시 첫 페이지로
        };

        // 빈 값 제거
        Object.keys(params).forEach(key => {
            if (params[key] === undefined || params[key] === '') {
                delete params[key];
            }
        });

        this.loadTransactionHistory(params);
    }

    /**
     * 페이지네이션 처리
     */
    handlePagination(event) {
        event.preventDefault();
        
        const page = parseInt(event.target.dataset.page);
        const limit = 20;
        const skip = (page - 1) * limit;

        this.loadTransactionHistory({ skip, limit });
    }

    /**
     * 복사 처리
     */
    async handleCopy(event) {
        const target = event.target.dataset.copy;
        const element = document.getElementById(target) || document.querySelector(`[data-copy-text="${target}"]`);
        
        let textToCopy = '';
        if (element) {
            textToCopy = element.textContent || element.value || element.dataset.copyText;
        } else {
            textToCopy = target;
        }

        try {
            await navigator.clipboard.writeText(textToCopy);
            this.showNotification('success', '클립보드에 복사되었습니다.');
        } catch (error) {
            console.error('복사 오류:', error);
            this.showNotification('error', '복사에 실패했습니다.');
        }
    }

    /**
     * 새로고침 처리
     */
    handleRefresh(event) {
        const target = event.target.dataset.refresh;
        
        switch (target) {
            case 'balance':
                if (window.walletManager) {
                    walletManager.loadBalance();
                }
                break;
            case 'history':
                this.loadTransactionHistory();
                break;
            case 'dashboard':
                this.loadDashboardData();
                break;
            default:
                window.location.reload();
        }
    }

    /**
     * 로딩 표시
     */
    showLoading(elementId, show) {
        const element = document.getElementById(elementId);
        if (element) {
            if (show) {
                element.classList.remove('hidden');
            } else {
                element.classList.add('hidden');
            }
        }
    }

    /**
     * 알림 표시
     */
    showNotification(type, message, duration = 5000) {
        // 기존 알림 제거
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        // 새 알림 생성
        const notification = document.createElement('div');
        notification.className = `notification alert alert-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // 자동 제거
        setTimeout(() => {
            notification.remove();
        }, duration);
    }

    /**
     * 문자열 자르기
     */
    truncateString(str, length) {
        if (str.length <= length) return str;
        return str.substring(0, length) + '...';
    }

    /**
     * 숫자 천 단위 구분자 추가
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    /**
     * 디바운스 함수
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// ===== 전역 유틸리티 함수들 =====

/**
 * 알림 표시 (전역 함수)
 */
function showAlert(type, message, duration = 5000) {
    window.mainApp.showNotification(type, message, duration);
}

/**
 * 모달 표시
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // 애니메이션 효과
        setTimeout(() => {
            modal.classList.add('active');
        }, 10);
    }
}

/**
 * 모달 닫기
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }, 300);
    }
}

/**
 * 폼 로딩 상태 설정
 */
function setFormLoading(form, loading) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const loadingSpinner = submitBtn?.querySelector('.btn-loading');
    const btnText = submitBtn?.querySelector('.btn-text');
    
    if (loading) {
        form.classList.add('form-loading');
        if (submitBtn) submitBtn.disabled = true;
        if (loadingSpinner) loadingSpinner.style.display = 'inline-block';
        if (btnText) btnText.style.opacity = '0.7';
    } else {
        form.classList.remove('form-loading');
        if (submitBtn) submitBtn.disabled = false;
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        if (btnText) btnText.style.opacity = '1';
    }
}

/**
 * 로딩 상태 표시/숨김
 */
function showLoading(elementId, show) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = show ? 'block' : 'none';
    }
}

/**
 * 날짜/시간 포맷팅
 */
function formatDateTime(dateString) {
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

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 숫자 포맷팅
 */
function formatAmount(amount, decimals = 8) {
    return parseFloat(amount).toFixed(decimals);
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * TRON 주소 검증
 */
function validateTronAddress(address) {
    return /^T[A-Za-z1-9]{33}$/.test(address);
}

/**
 * 이메일 검증
 */
function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * 클립보드 복사
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('success', '클립보드에 복사되었습니다.');
        }).catch(() => {
            showAlert('warning', '복사에 실패했습니다.');
        });
    } else {
        // 폴백 방법
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showAlert('success', '클립보드에 복사되었습니다.');
        } catch (err) {
            showAlert('warning', '복사에 실패했습니다.');
        }
        document.body.removeChild(textArea);
    }
}

/**
 * 디바운스 함수 (전역)
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 문자열 자르기
 */
function truncateString(str, length) {
    if (!str) return '';
    if (str.length <= length) return str;
    return str.substring(0, length) + '...';
}

/**
 * 거래 타입 아이콘 반환
 */
function getTransactionIcon(type) {
    const icons = {
        'TRANSFER_OUT': 'fa-arrow-up',
        'TRANSFER_IN': 'fa-arrow-down', 
        'WITHDRAWAL': 'fa-sign-out-alt',
        'DEPOSIT': 'fa-sign-in-alt'
    };
    return icons[type] || 'fa-exchange-alt';
}

/**
 * 거래 타입 이름 반환
 */
function getTransactionTypeName(type) {
    const names = {
        'TRANSFER_OUT': '이체 보내기',
        'TRANSFER_IN': '이체 받기',
        'WITHDRAWAL': '출금',
        'DEPOSIT': '입금'
    };
    return names[type] || type;
}

/**
 * 상태 아이콘 반환
 */
function getStatusIcon(status) {
    const icons = {
        'PENDING': 'fa-clock',
        'COMPLETED': 'fa-check',
        'FAILED': 'fa-times',
        'CANCELLED': 'fa-ban'
    };
    return icons[status] || 'fa-question';
}

/**
 * 상태 이름 반환
 */
function getStatusName(status) {
    const names = {
        'PENDING': '대기 중',
        'COMPLETED': '완료',
        'FAILED': '실패',
        'CANCELLED': '취소'
    };
    return names[status] || status;
}

/**
 * 금액 클래스 반환
 */
function getAmountClass(type) {
    return (type === 'TRANSFER_IN' || type === 'DEPOSIT') ? 'positive' : 'negative';
}

/**
 * 금액 접두사 반환
 */
function getAmountPrefix(type) {
    return (type === 'TRANSFER_IN' || type === 'DEPOSIT') ? '+' : '-';
}

/**
 * 로컬 스토리지 헬퍼
 */
const storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('로컬 스토리지 저장 오류:', error);
        }
    },
    
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('로컬 스토리지 읽기 오류:', error);
            return defaultValue;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('로컬 스토리지 삭제 오류:', error);
        }
    },
    
    clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('로컬 스토리지 초기화 오류:', error);
        }
    }
};

/**
 * 블록체인 탐색기 열기
 */
function openBlockchainExplorer(txHash) {
    const url = `https://tronscan.org/#/transaction/${txHash}`;
    window.open(url, '_blank');
}

/**
 * 페이지 리다이렉트
 */
function redirectTo(page) {
    window.location.href = page;
}

/**
 * 현재 페이지 확인
 */
function getCurrentPage() {
    const path = window.location.pathname;
    const filename = path.split('/').pop() || 'index.html';
    return filename.replace('.html', '');
}

/**
 * URL 매개변수 가져오기
 */
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * 네트워크 상태 확인
 */
function checkNetworkConnection() {
    if (!navigator.onLine) {
        showAlert('warning', '인터넷 연결을 확인해주세요.');
        return false;
    }
    return true;
}

/**
 * 모바일 기기 감지
 */
function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * 브라우저 지원 확인
 */
function checkBrowserSupport() {
    const isSupported = 'fetch' in window && 'localStorage' in window && 'Promise' in window;
    if (!isSupported) {
        showAlert('danger', '지원되지 않는 브라우저입니다. 최신 버전으로 업데이트해주세요.');
    }
    return isSupported;
}

// 초기 브라우저 지원 확인
checkBrowserSupport();
