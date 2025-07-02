"""
USDT TRC20 지갑 서비스의 데이터베이스 모델.
사용자, 잔액, 트랜잭션에 대한 SQLAlchemy 모델을 정의합니다.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from decimal import Decimal as PyDecimal

from .core.db import Base


class TransactionType(PyEnum):
    """트랜잭션 유형 열거형."""
    DEPOSIT = "deposit"       # 입금
    WITHDRAWAL = "withdrawal" # 출금
    TRANSFER = "transfer"     # 이체
    PAYMENT = "payment"       # 결제


class TransactionStatus(PyEnum):
    """트랜잭션 상태 열거형."""
    PENDING = "pending"       # 대기 중
    COMPLETED = "completed"   # 완료
    FAILED = "failed"         # 실패
    CANCELLED = "cancelled"   # 취소


class User(Base):
    """
    시스템 사용자를 나타내는 사용자 모델.
    
    속성:
        id: 기본 키
        email: 고유한 이메일 주소
        password_hash: 해시된 패스워드
        is_admin: 관리자 권한 플래그
        is_active: 계정 상태 플래그
        created_at: 계정 생성 타임스탬프
        updated_at: 마지막 업데이트 타임스탬프
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 정의
    balances = relationship("Balance", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", foreign_keys="Transaction.user_id", cascade="all, delete-orphan")


class Balance(Base):
    """
    사용자 자산 잔액을 나타내는 잔액 모델.
    
    속성:
        id: 기본 키
        user_id: 사용자 외래 키
        asset: 자산 심볼 (예: 'USDT', 'TRX')
        amount: 현재 잔액 금액
        frozen_amount: 현재 동결/잠금된 금액
        updated_at: 마지막 잔액 업데이트 타임스탬프
    """
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset = Column(String, nullable=False, default="USDT")
    amount = Column(DECIMAL(precision=18, scale=8), nullable=False, default=PyDecimal('0.00000000'))
    frozen_amount = Column(DECIMAL(precision=18, scale=8), nullable=False, default=PyDecimal('0.00000000'))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # 관계 정의
    user = relationship("User", back_populates="balances")

    # 복합 고유 제약 조건
    __table_args__ = (
        {"schema": None},  # 필요시 여기에 스키마 추가 가능
    )


class Transaction(Base):
    """
    Transaction model representing all transaction records.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to user
        type: Transaction type (deposit/withdrawal/transfer/payment)
        amount: Transaction amount
        asset: Asset symbol
        status: Transaction status
        ref_tx_id: Reference transaction ID (blockchain hash for on-chain transactions)
        related_user_id: Related user ID (for internal transfers)
        memo: Transaction memo/description
        fee_amount: Transaction fee amount
        created_at: Transaction creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(DECIMAL(precision=18, scale=8), nullable=False)
    asset = Column(String, nullable=False, default="USDT")
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    ref_tx_id = Column(String, nullable=True)  # 블록체인 트랜잭션 해시
    related_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 내부 송금용
    memo = Column(Text, nullable=True)
    fee_amount = Column(DECIMAL(precision=18, scale=8), nullable=False, default=PyDecimal('0.00000000'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    user = relationship("User", back_populates="transactions", foreign_keys=[user_id])
    related_user = relationship("User", foreign_keys=[related_user_id])


class DepositAddress(Base):
    """
    Deposit address model for tracking user-specific deposit addresses.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to user
        address: Tron wallet address
        memo: Deposit memo/tag for identification
        is_active: Address status flag
        created_at: Creation timestamp
    """
    __tablename__ = "deposit_addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address = Column(String, nullable=False)
    memo = Column(String, nullable=True)  # 입금 식별을 위한 선택적 메모
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    user = relationship("User")


class WithdrawalRequest(Base):
    """
    Withdrawal request model for tracking withdrawal approvals.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to user
        amount: Withdrawal amount
        asset: Asset symbol
        destination_address: Target wallet address
        status: Request status
        admin_user_id: Admin who processed the request
        processed_at: Processing timestamp
        transaction_id: Related transaction ID after processing
        created_at: Request creation timestamp
    """
    __tablename__ = "withdrawal_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(precision=18, scale=8), nullable=False)
    asset = Column(String, nullable=False, default="USDT")
    destination_address = Column(String, nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    memo = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    user = relationship("User", foreign_keys=[user_id])
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    transaction = relationship("Transaction")
