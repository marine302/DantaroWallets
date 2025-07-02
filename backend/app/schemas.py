"""
Pydantic schemas for request/response validation.
Defines data models for API input/output serialization.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, validator, Field
from enum import Enum

from .models import TransactionType, TransactionStatus


# 기본 스키마
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        use_enum_values = True


# 사용자 스키마
class UserBase(BaseSchema):
    """Base user schema with common fields."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserLogin(BaseSchema):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime


class UserProfile(UserResponse):
    """Extended user profile schema."""
    pass


# 인증 스키마
class Token(BaseSchema):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseSchema):
    """Schema for token data."""
    user_id: Optional[int] = None


# 잔액 스키마
class BalanceBase(BaseSchema):
    """Base balance schema."""
    asset: str = "USDT"
    amount: Decimal = Field(default=Decimal('0.00000000'), ge=0)


class BalanceResponse(BalanceBase):
    """Schema for balance response."""
    id: int
    user_id: int
    frozen_amount: Decimal
    updated_at: Optional[datetime] = None


class BalanceUpdate(BaseSchema):
    """Schema for balance updates."""
    amount: Decimal
    asset: str = "USDT"


# 트랜잭션 스키마
class TransactionBase(BaseSchema):
    """Base transaction schema."""
    type: TransactionType
    amount: Decimal = Field(..., gt=0, description="Transaction amount must be positive")
    asset: str = "USDT"
    memo: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for transaction creation."""
    related_user_id: Optional[int] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: int
    user_id: int
    status: TransactionStatus
    ref_tx_id: Optional[str] = None
    related_user_id: Optional[int] = None
    fee_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None


class TransactionHistory(BaseSchema):
    """Schema for transaction history response."""
    transactions: List[TransactionResponse]
    total_count: int
    page: int
    page_size: int


# 송금 스키마
class InternalTransfer(BaseSchema):
    """Schema for internal transfers between users."""
    recipient_email: EmailStr
    amount: Decimal = Field(..., gt=0, description="Transfer amount must be positive")
    asset: str = "USDT"
    memo: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Transfer amount must be positive')
        if v > Decimal('1000000'):  # 최대 송금 한도
            raise ValueError('Transfer amount exceeds maximum limit')
        return v


class TransferResponse(BaseSchema):
    """Schema for transfer response."""
    transaction_id: int
    status: str
    message: str


# 출금 스키마
class WithdrawalRequest(BaseSchema):
    """Schema for withdrawal requests."""
    amount: Decimal = Field(..., gt=0, description="Withdrawal amount must be positive")
    asset: str = "USDT"
    destination_address: str = Field(..., min_length=34, max_length=34, description="Valid Tron address")
    memo: Optional[str] = None
    
    @validator('destination_address')
    def validate_tron_address(cls, v):
        if not v.startswith('T') or len(v) != 34:
            raise ValueError('Invalid Tron address format')
        return v


class WithdrawalResponse(BaseSchema):
    """Schema for withdrawal response."""
    request_id: int
    status: str
    message: str
    estimated_fee: Decimal


class WithdrawalApproval(BaseSchema):
    """Schema for withdrawal approval."""
    request_id: int
    approved: bool
    admin_memo: Optional[str] = None


# 입금 스키마
class DepositAddress(BaseSchema):
    """Schema for deposit address."""
    address: str
    memo: Optional[str] = None
    qr_code: Optional[str] = None


class DepositCheck(BaseSchema):
    """Schema for deposit check response."""
    found_deposits: List[TransactionResponse]
    message: str


# 관리자 스키마
class AdminBalanceView(BaseSchema):
    """Schema for admin balance overview."""
    user_id: int
    user_email: str
    balances: List[BalanceResponse]
    total_balance_usd: Decimal


class AdminUserList(BaseSchema):
    """Schema for admin user list."""
    users: List[UserResponse]
    total_count: int


class AdminWithdrawalList(BaseSchema):
    """Schema for admin withdrawal requests list."""
    requests: List[dict]  # 출금 요청 모델 기반으로 적절히 타입 지정됨
    total_count: int


class AdminSendTransaction(BaseSchema):
    """Schema for admin-initiated blockchain transactions."""
    to_address: str = Field(..., min_length=34, max_length=34)
    amount: Decimal = Field(..., gt=0)
    asset: str = "USDT"
    memo: Optional[str] = None


# 응답 스키마
class SuccessResponse(BaseSchema):
    """Generic success response schema."""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseSchema):
    """Generic error response schema."""
    success: bool = False
    error: str
    details: Optional[str] = None


# 페이지네이션 스키마
class PaginationParams(BaseSchema):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseSchema):
    """Base schema for paginated responses."""
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_prev: bool
