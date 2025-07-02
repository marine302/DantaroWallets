/**
 * 지갑 기능 관리 모듈
 * 잔액 조회, 이체, 출금 등 지갑 관련 기능을 담당합니다.
 */

class WalletManager {
    constructor() {
        this.balance = {
            USDT: 0,
            TRX: 0
        };
        this.init();
    }

    /**
     * 초기화
     */
    init() {
        this.setupEventListeners();
        this.loadBalance();
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 이체 폼
        const transferForm = document.getElementById('transferForm');
        if (transferForm) {
            transferForm.addEventListener('submit', (e) => this.handleTransfer(e));
        }

        // 출금 폼
        const withdrawForm = document.getElementById('withdrawForm');
        if (withdrawForm) {
            withdrawForm.addEventListener('submit', (e) => this.handleWithdraw(e));
        }

        // 입금 주소 생성 버튼
        const depositBtn = document.getElementById('generateDepositBtn');
        if (depositBtn) {
            depositBtn.addEventListener('click', () => this.generateDepositAddress());
        }

        // 잔액 새로고침 버튼
        const refreshBtn = document.getElementById('refreshBalanceBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadBalance());
        }

        // 모달 닫기 버튼들
        const modalCloseBtns = document.querySelectorAll('.modal-close');
        modalCloseBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.closeModal(e.target.closest('.modal')));
        });

        // 모달 외부 클릭 시 닫기
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            });
        });

        // 액션 버튼들
        const actionBtns = document.querySelectorAll('.action-btn');
        actionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleActionClick(e));
        });
    }

    /**
     * 잔액 로드
     */
    async loadBalance() {
        try {
            this.showLoading('balance-loading', true);
            
            const balances = await walletAPI.getBalance();
            
            // 잔액 데이터 업데이트
            balances.forEach(balance => {
                this.balance[balance.asset] = parseFloat(balance.amount);
            });

            // UI 업데이트
            this.updateBalanceDisplay();
            
        } catch (error) {
            console.error('잔액 로드 오류:', error);
            this.showAlert('danger', '잔액을 불러오는데 실패했습니다.');
        } finally {
            this.showLoading('balance-loading', false);
        }
    }

    /**
     * 잔액 표시 업데이트
     */
    updateBalanceDisplay() {
        // 메인 USDT 잔액
        const usdtBalanceElement = document.getElementById('usdtBalance');
        if (usdtBalanceElement) {
            usdtBalanceElement.textContent = walletAPI.formatAmount(this.balance.USDT);
        }

        // TRX 잔액 (가스비용)
        const trxBalanceElement = document.getElementById('trxBalance');
        if (trxBalanceElement) {
            trxBalanceElement.textContent = walletAPI.formatAmount(this.balance.TRX, 6);
        }

        // 대시보드 통계
        const totalBalanceElement = document.getElementById('totalBalance');
        if (totalBalanceElement) {
            totalBalanceElement.textContent = walletAPI.formatAmount(this.balance.USDT);
        }
    }

    /**
     * 액션 버튼 클릭 처리
     */
    handleActionClick(event) {
        event.preventDefault();
        const action = event.currentTarget.dataset.action;
        
        switch (action) {
            case 'transfer':
                this.showModal('transferModal');
                break;
            case 'withdraw':
                this.showModal('withdrawModal');
                break;
            case 'deposit':
                this.showModal('depositModal');
                this.generateDepositAddress();
                break;
            case 'history':
                window.location.href = '/history.html';
                break;
        }
    }

    /**
     * 이체 처리
     */
    async handleTransfer(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const toEmail = formData.get('toEmail');
        const amount = parseFloat(formData.get('amount'));
        const memo = formData.get('memo') || '';

        // 유효성 검사
        if (!this.validateEmail(toEmail)) {
            this.showAlert('danger', '올바른 이메일 주소를 입력해주세요.');
            return;
        }

        if (amount <= 0) {
            this.showAlert('danger', '이체 금액은 0보다 커야 합니다.');
            return;
        }

        if (amount > this.balance.USDT) {
            this.showAlert('danger', '잔액이 부족합니다.');
            return;
        }

        this.setFormLoading(form, true);
        
        try {
            const response = await walletAPI.transfer(toEmail, amount, 'USDT', memo);
            
            this.showAlert('success', '이체가 완료되었습니다!');
            this.closeModal(document.getElementById('transferModal'));
            form.reset();
            
            // 잔액 새로고침
            setTimeout(() => {
                this.loadBalance();
            }, 1000);
            
        } catch (error) {
            this.showAlert('danger', error.message || '이체에 실패했습니다.');
        } finally {
            this.setFormLoading(form, false);
        }
    }

    /**
     * 출금 처리
     */
    async handleWithdraw(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const address = formData.get('address');
        const amount = parseFloat(formData.get('amount'));
        const memo = formData.get('memo') || '';

        // 유효성 검사
        if (!this.validateTronAddress(address)) {
            this.showAlert('danger', '올바른 트론 주소를 입력해주세요.');
            return;
        }

        if (amount <= 0) {
            this.showAlert('danger', '출금 금액은 0보다 커야 합니다.');
            return;
        }

        if (amount > this.balance.USDT) {
            this.showAlert('danger', '잔액이 부족합니다.');
            return;
        }

        if (amount < 10) {
            this.showAlert('danger', '최소 출금 금액은 10 USDT입니다.');
            return;
        }

        // 확인 메시지
        const fee = amount * 0.005; // 0.5% 수수료
        const finalAmount = amount - fee;
        if (!confirm(`출금 신청하시겠습니까?\n\n금액: ${amount} USDT\n수수료: ${fee.toFixed(8)} USDT\n실제 받을 금액: ${finalAmount.toFixed(8)} USDT`)) {
            return;
        }

        this.setFormLoading(form, true);
        
        try {
            const response = await walletAPI.withdraw(address, amount, 'USDT', memo);
            
            this.showAlert('success', '출금 신청이 완료되었습니다. 관리자 승인 후 처리됩니다.');
            this.closeModal(document.getElementById('withdrawModal'));
            form.reset();
            
            // 잔액 새로고침
            setTimeout(() => {
                this.loadBalance();
            }, 1000);
            
        } catch (error) {
            this.showAlert('danger', error.message || '출금 신청에 실패했습니다.');
        } finally {
            this.setFormLoading(form, false);
        }
    }

    /**
     * 입금 주소 생성
     */
    async generateDepositAddress() {
        try {
            this.showLoading('deposit-loading', true);
            
            const response = await walletAPI.getDepositAddress('USDT');
            
            const addressElement = document.getElementById('depositAddress');
            const qrCodeElement = document.getElementById('depositQRCode');
            
            if (addressElement) {
                addressElement.textContent = response.address;
            }

            // QR 코드 생성 (QR.js 라이브러리 사용 시)
            if (qrCodeElement && typeof QR !== 'undefined') {
                qrCodeElement.innerHTML = '';
                QR.toCanvas(qrCodeElement, response.address, (error) => {
                    if (error) console.error('QR 코드 생성 오류:', error);
                });
            }
            
        } catch (error) {
            console.error('입금 주소 생성 오류:', error);
            this.showAlert('danger', '입금 주소를 생성하는데 실패했습니다.');
        } finally {
            this.showLoading('deposit-loading', false);
        }
    }

    /**
     * 주소 복사
     */
    copyAddress() {
        const addressElement = document.getElementById('depositAddress');
        if (addressElement) {
            navigator.clipboard.writeText(addressElement.textContent).then(() => {
                this.showAlert('success', '주소가 클립보드에 복사되었습니다.');
            }).catch(() => {
                this.showAlert('danger', '복사에 실패했습니다.');
            });
        }
    }

    /**
     * 모달 표시
     */
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
        }
    }

    /**
     * 모달 닫기
     */
    closeModal(modal) {
        if (modal) {
            modal.classList.remove('show');
        }
    }

    /**
     * 폼 로딩 상태 설정
     */
    setFormLoading(form, isLoading) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const inputs = form.querySelectorAll('input, textarea');
        
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="spinner"></div> 처리 중...';
            inputs.forEach(input => input.disabled = true);
        } else {
            submitBtn.disabled = false;
            const originalText = submitBtn.dataset.originalText || '확인';
            submitBtn.innerHTML = originalText;
            inputs.forEach(input => input.disabled = false);
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
     * 이메일 유효성 검사
     */
    validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    /**
     * 트론 주소 유효성 검사
     */
    validateTronAddress(address) {
        // 트론 주소는 T로 시작하고 34자리
        const regex = /^T[A-Za-z0-9]{33}$/;
        return regex.test(address);
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

        // 컨테이너 상단에 삽입
        const container = document.querySelector('.main-content .container');
        if (container) {
            container.insertBefore(alert, container.firstChild);
        }

        // 자동 제거
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    /**
     * 통계 데이터 로드 (대시보드용)
     */
    async loadDashboardStats() {
        try {
            // 최근 거래 내역
            const transactions = await walletAPI.getTransactions({ limit: 5 });
            this.updateRecentTransactions(transactions.transactions || []);
            
        } catch (error) {
            console.error('대시보드 통계 로드 오류:', error);
        }
    }

    /**
     * 최근 거래 표시 업데이트
     */
    updateRecentTransactions(transactions) {
        const container = document.getElementById('recentTransactions');
        if (!container) return;

        if (transactions.length === 0) {
            container.innerHTML = '<p class="text-secondary">최근 거래가 없습니다.</p>';
            return;
        }

        const html = transactions.map(tx => `
            <div class="transaction-item">
                <div class="transaction-info">
                    <span class="transaction-type">${walletAPI.getTypeText(tx.type)}</span>
                    <span class="transaction-amount ${tx.type === 'withdrawal' ? 'text-danger' : 'text-success'}">
                        ${tx.type === 'withdrawal' ? '-' : '+'}${walletAPI.formatAmount(tx.amount)} ${tx.asset}
                    </span>
                </div>
                <div class="transaction-meta">
                    <span class="transaction-date">${walletAPI.formatDate(tx.created_at)}</span>
                    <span class="badge badge-${this.getStatusBadgeClass(tx.status)}">
                        ${walletAPI.getStatusText(tx.status)}
                    </span>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    /**
     * 상태에 따른 배지 클래스 반환
     */
    getStatusBadgeClass(status) {
        const classMap = {
            'pending': 'warning',
            'completed': 'success',
            'failed': 'danger',
            'cancelled': 'danger'
        };
        return classMap[status] || 'info';
    }
}

// 전역 인스턴스 생성
window.walletManager = new WalletManager();
