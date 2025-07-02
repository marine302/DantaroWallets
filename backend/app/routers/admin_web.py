"""
관리자 웹 페이지 라우터입니다.
관리자가 사용할 수 있는 웹 인터페이스를 제공합니다.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from ..core.db import get_db
from ..crud import crud_user, crud_balance, crud_withdrawal_request, crud_transaction
from ..deps import get_current_admin_user_from_cookie, get_current_user_optional
from ..utils.security import create_access_token, verify_password
from .. import models, schemas

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """관리자 로그인 페이지를 표시합니다."""
    return templates.TemplateResponse("admin/login.html", {"request": request, "admin": False})


@router.get("/login", response_class=HTMLResponse)
async def admin_login_get(request: Request):
    """관리자 로그인 페이지를 표시합니다."""
    return templates.TemplateResponse("admin/login.html", {"request": request, "admin": False})


@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """관리자 로그인을 처리합니다."""
    user = crud_user.get_by_email(db, email=email)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin/login.html", 
            {"request": request, "error": "잘못된 이메일 또는 비밀번호입니다.", "admin": False}
        )
    
    if not user.is_admin:
        return templates.TemplateResponse(
            "admin/login.html", 
            {"request": request, "error": "관리자 권한이 필요합니다.", "admin": False}
        )
    
    # JWT 토큰 생성
    access_token = create_access_token(subject=str(user.id))
    
    # 대시보드로 리다이렉트하면서 토큰을 쿠키에 설정
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_admin: models.User = Depends(get_current_admin_user_from_cookie),
    db: Session = Depends(get_db)
):
    """관리자 대시보드를 표시합니다."""
    # 통계 데이터 수집
    total_users = db.query(models.User).count()
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    pending_withdrawals = db.query(models.WithdrawalRequest).filter(
        models.WithdrawalRequest.status == models.TransactionStatus.PENDING
    ).count()
    
    # 최근 거래 내역
    recent_transactions = db.query(models.Transaction).order_by(
        models.Transaction.created_at.desc()
    ).limit(10).all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin": True,
        "current_user": current_admin,
        "total_users": total_users,
        "active_users": active_users,
        "pending_withdrawals": pending_withdrawals,
        "total_balance": 0.0,  # 일단 0으로 설정
        "recent_transactions": recent_transactions,
        "current_time": datetime.now(),
        "format_usdt": lambda x: f"{x:.8f}"
    })


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    current_admin: models.User = Depends(get_current_admin_user_from_cookie),
    db: Session = Depends(get_db)
):
    """사용자 관리 페이지를 표시합니다."""
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "admin": True,
        "current_user": current_admin,
        "users": users
    })


@router.get("/withdrawals", response_class=HTMLResponse)
async def admin_withdrawals_page(
    request: Request,
    current_admin: models.User = Depends(get_current_admin_user_from_cookie),
    db: Session = Depends(get_db)
):
    """출금 승인 페이지를 표시합니다."""
    withdrawals = db.query(models.WithdrawalRequest).order_by(
        models.WithdrawalRequest.created_at.desc()
    ).all()
    
    return templates.TemplateResponse("admin/withdrawals.html", {
        "request": request,
        "admin": True,
        "current_user": current_admin,
        "withdrawals": withdrawals
    })


@router.post("/withdrawals/{withdrawal_id}/approve")
async def approve_withdrawal(
    withdrawal_id: int,
    current_admin: models.User = Depends(get_current_admin_user_from_cookie),
    db: Session = Depends(get_db)
):
    """출금 요청을 승인합니다."""
    withdrawal = crud_withdrawal_request.approve_request(
        db=db, 
        request_id=withdrawal_id, 
        admin_user_id=current_admin.id,  # type: ignore
        approved=True
    )
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="출금 요청을 찾을 수 없습니다.")
    
    return RedirectResponse(url="/admin/withdrawals", status_code=302)


@router.post("/withdrawals/{withdrawal_id}/reject")
async def reject_withdrawal(
    withdrawal_id: int,
    current_admin: models.User = Depends(get_current_admin_user_from_cookie),
    db: Session = Depends(get_db)
):
    """출금 요청을 거부합니다."""
    withdrawal = crud_withdrawal_request.approve_request(
        db=db, 
        request_id=withdrawal_id, 
        admin_user_id=current_admin.id,  # type: ignore
        approved=False
    )
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="출금 요청을 찾을 수 없습니다.")
    
    return RedirectResponse(url="/admin/withdrawals", status_code=302)


@router.get("/logout")
async def admin_logout():
    """관리자 로그아웃을 처리합니다."""
    response = RedirectResponse(url="/admin/", status_code=302)
    response.delete_cookie(key="access_token")
    return response
