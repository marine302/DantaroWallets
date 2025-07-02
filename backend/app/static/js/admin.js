// 관리자 페이지 JavaScript 기능

document.addEventListener('DOMContentLoaded', function() {
    // 현재 페이지에 따른 네비게이션 활성화
    setActiveNavigation();
    
    // 테이블 기능 초기화
    initializeTableFeatures();
    
    // 폼 유효성 검사 초기화
    initializeFormValidation();
    
    // 모달 이벤트 초기화
    initializeModals();
    
    // 알림 자동 숨김
    initializeAlerts();
    
    // 페이지 로딩 인디케이터
    initializeLoadingIndicators();
});

// 네비게이션 활성화 설정
function setActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');
        
        if (href && currentPath.includes(href.split('/').pop())) {
            link.classList.add('active');
        }
    });
}

// 테이블 기능 초기화
function initializeTableFeatures() {
    // 테이블 행 클릭 이벤트
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', function(e) {
            if (!e.target.closest('button') && !e.target.closest('a')) {
                const selected = document.querySelector('table tbody tr.selected');
                if (selected) selected.classList.remove('selected');
                this.classList.add('selected');
            }
        });
    });
    
    // 테이블 정렬 기능
    initializeTableSort();
}

// 테이블 정렬 기능
function initializeTableSort() {
    const headers = document.querySelectorAll('table thead th[data-sort]');
    
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const column = this.dataset.sort;
            const isAsc = this.classList.contains('sort-asc');
            
            // 정렬 방향 토글
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            this.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
            
            // 행 정렬
            rows.sort((a, b) => {
                const aValue = a.querySelector(`[data-value="${column}"]`)?.textContent || 
                              a.children[parseInt(column)]?.textContent || '';
                const bValue = b.querySelector(`[data-value="${column}"]`)?.textContent || 
                              b.children[parseInt(column)]?.textContent || '';
                
                const compare = aValue.localeCompare(bValue, 'ko', { numeric: true });
                return isAsc ? -compare : compare;
            });
            
            // DOM 업데이트
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// 폼 유효성 검사
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
        
        // 실시간 유효성 검사
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
    });
}

// 개별 필드 유효성 검사
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const required = field.hasAttribute('required');
    
    // 필수 필드 검사
    if (required && !value) {
        setFieldError(field, '이 필드는 필수입니다.');
        return false;
    }
    
    // 이메일 검사
    if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            setFieldError(field, '올바른 이메일 주소를 입력하세요.');
            return false;
        }
    }
    
    // 비밀번호 검사
    if (field.name === 'password' && value) {
        if (value.length < 8) {
            setFieldError(field, '비밀번호는 최소 8자 이상이어야 합니다.');
            return false;
        }
    }
    
    clearFieldError(field);
    return true;
}

// 전체 폼 유효성 검사
function validateForm(form) {
    const fields = form.querySelectorAll('input, select, textarea');
    let isValid = true;
    
    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// 필드 오류 표시
function setFieldError(field, message) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    
    let feedback = field.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
}

// 필드 오류 제거
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
    
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

// 모달 초기화
function initializeModals() {
    // 확인 모달
    window.showConfirmModal = function(title, message, callback) {
        const modal = document.getElementById('confirmModal');
        if (modal) {
            modal.querySelector('.modal-title').textContent = title;
            modal.querySelector('.modal-body').innerHTML = message;
            
            const confirmBtn = modal.querySelector('.btn-danger');
            confirmBtn.onclick = function() {
                callback();
                bootstrap.Modal.getInstance(modal).hide();
            };
            
            new bootstrap.Modal(modal).show();
        }
    };
    
    // 사용자 상태 토글
    window.toggleUserStatus = function(userId, currentStatus) {
        const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
        const statusText = newStatus === 'active' ? '활성화' : '비활성화';
        
        showConfirmModal(
            '사용자 상태 변경',
            `정말로 이 사용자를 ${statusText}하시겠습니까?`,
            function() {
                updateUserStatus(userId, newStatus);
            }
        );
    };
    
    // 출금 승인/거부
    window.handleWithdrawal = function(withdrawalId, action) {
        const actionText = action === 'approve' ? '승인' : '거부';
        
        showConfirmModal(
            `출금 ${actionText}`,
            `정말로 이 출금 요청을 ${actionText}하시겠습니까?`,
            function() {
                processWithdrawal(withdrawalId, action);
            }
        );
    };
}

// 사용자 상태 업데이트
async function updateUserStatus(userId, status) {
    try {
        showLoading();
        
        const response = await fetch(`/api/admin/users/${userId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({ status: status })
        });
        
        if (response.ok) {
            location.reload(); // 페이지 새로고침으로 변경 반영
            showAlert('사용자 상태가 성공적으로 변경되었습니다.', 'success');
        } else {
            throw new Error('상태 변경에 실패했습니다.');
        }
    } catch (error) {
        showAlert('오류가 발생했습니다: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

// 출금 처리
async function processWithdrawal(withdrawalId, action) {
    try {
        showLoading();
        
        const response = await fetch(`/api/admin/withdrawals/${withdrawalId}/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (response.ok) {
            location.reload(); // 페이지 새로고침으로 변경 반영
            showAlert(`출금이 성공적으로 ${action === 'approve' ? '승인' : '거부'}되었습니다.`, 'success');
        } else {
            throw new Error('처리에 실패했습니다.');
        }
    } catch (error) {
        showAlert('오류가 발생했습니다: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

// 인증 토큰 가져오기 (쿠키에서)
function getAuthToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'admin_token') {
            return value;
        }
    }
    return null;
}

// 알림 표시
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // 자동 제거
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// 알림 컨테이너 생성
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.minWidth = '300px';
    document.body.appendChild(container);
    return container;
}

// 로딩 표시
function showLoading() {
    const loading = document.getElementById('loadingOverlay') || createLoadingOverlay();
    loading.style.display = 'flex';
}

// 로딩 숨김
function hideLoading() {
    const loading = document.getElementById('loadingOverlay');
    if (loading) {
        loading.style.display = 'none';
    }
}

// 로딩 오버레이 생성
function createLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="loading"></div>
            <span class="ms-2">처리 중...</span>
        </div>
    `;
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 10000;
        display: none;
        color: white;
    `;
    document.body.appendChild(overlay);
    return overlay;
}

// 알림 자동 숨김 초기화
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });
}

// 로딩 인디케이터 초기화
function initializeLoadingIndicators() {
    // 폼 제출시 로딩 표시
    document.addEventListener('submit', function(e) {
        if (e.target.tagName === 'FORM') {
            const submitBtn = e.target.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="loading"></span> 처리 중...';
                submitBtn.disabled = true;
                
                // 3초 후 원복 (실패 케이스 대비)
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 3000);
            }
        }
    });
    
    // AJAX 요청시 로딩 표시
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30초 타임아웃
        
        args[1] = args[1] || {};
        args[1].signal = controller.signal;
        
        return originalFetch.apply(this, args)
            .finally(() => clearTimeout(timeoutId));
    };
}

// 유틸리티 함수들
window.formatCurrency = function(amount) {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW'
    }).format(amount);
};

window.formatDate = function(dateString) {
    return new Date(dateString).toLocaleString('ko-KR');
};

window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('클립보드에 복사되었습니다.', 'success');
    }).catch(() => {
        showAlert('복사에 실패했습니다.', 'danger');
    });
};

// 반응형 사이드바 토글
window.toggleSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
};

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            bootstrap.Modal.getInstance(modal)?.hide();
        });
    }
});

// 페이지 떠날 때 확인 (변경사항 있을 경우)
window.addEventListener('beforeunload', function(e) {
    const forms = document.querySelectorAll('form.changed');
    if (forms.length > 0) {
        e.preventDefault();
        e.returnValue = '변경사항이 저장되지 않았습니다. 정말로 페이지를 떠나시겠습니까?';
    }
});

// 폼 변경 감지
document.addEventListener('input', function(e) {
    if (e.target.form) {
        e.target.form.classList.add('changed');
    }
});

document.addEventListener('submit', function(e) {
    if (e.target.tagName === 'FORM') {
        e.target.classList.remove('changed');
    }
});
