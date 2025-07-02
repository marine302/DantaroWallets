"""
CRUD operations for database entities.
Handles Create, Read, Update, Delete operations with business logic.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from decimal import Decimal
from datetime import datetime

from . import models, schemas
from .utils.security import get_password_hash, verify_password


class CRUDUser:
    """CRUD operations for User model."""
    
    def get(self, db: Session, user_id: int) -> Optional[models.User]:
        """Get user by ID."""
        return db.query(models.User).filter(models.User.id == user_id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[models.User]:
        """Get user by email."""
        return db.query(models.User).filter(models.User.email == email).first()
    
    def create(self, db: Session, user_create: schemas.UserCreate) -> models.User:
        """Create new user."""
        hashed_password = get_password_hash(user_create.password)
        db_user = models.User(
            email=user_create.email,
            password_hash=hashed_password,
            is_admin=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 초기 USDT 잔액 생성
        self._create_initial_balance(db, db_user.id)  # type: ignore
        
        return db_user
    
    def authenticate(self, db: Session, email: str, password: str) -> Optional[models.User]:
        """Authenticate user with email and password."""
        user = self.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, str(user.password_hash)):  # type: ignore
            return None
        return user
    
    def is_active(self, user: models.User) -> bool:
        """Check if user is active."""
        return bool(user.is_active)  # type: ignore
    
    def is_admin(self, user: models.User) -> bool:
        """Check if user is admin."""
        return bool(user.is_admin)  # type: ignore
    
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
        """Get multiple users with pagination."""
        return db.query(models.User).offset(skip).limit(limit).all()
    
    def _create_initial_balance(self, db: Session, user_id: int) -> None:
        """Create initial balance record for new user."""
        initial_balance = models.Balance(
            user_id=user_id,
            asset="USDT",
            amount=Decimal('0.00000000'),
            frozen_amount=Decimal('0.00000000')
        )
        db.add(initial_balance)
        db.commit()


class CRUDBalance:
    """CRUD operations for Balance model."""
    
    def get_user_balance(self, db: Session, user_id: int, asset: str = "USDT") -> Optional[models.Balance]:
        """Get user balance for specific asset."""
        return db.query(models.Balance).filter(
            and_(models.Balance.user_id == user_id, models.Balance.asset == asset)
        ).first()
    
    def get_user_balances(self, db: Session, user_id: int) -> List[models.Balance]:
        """Get all balances for a user."""
        return db.query(models.Balance).filter(models.Balance.user_id == user_id).all()
    
    def update_balance(
        self, 
        db: Session, 
        user_id: int, 
        asset: str, 
        amount_change: Decimal,
        freeze_change: Decimal = Decimal('0')
    ) -> Optional[models.Balance]:
        """
        Update user balance atomically.
        
        Args:
            db: Database session
            user_id: User ID
            asset: Asset symbol
            amount_change: Amount to add/subtract (can be negative)
            freeze_change: Amount to freeze/unfreeze (can be negative)
            
        Returns:
            Updated balance object or None if insufficient funds
        """
        balance = self.get_user_balance(db, user_id, asset)
        if not balance:
            # 잔액이 존재하지 않으면 생성
            balance = models.Balance(
                user_id=user_id,
                asset=asset,
                amount=Decimal('0.00000000'),
                frozen_amount=Decimal('0.00000000')
            )
            db.add(balance)
            db.flush()
        
        current_amount = Decimal(str(balance.amount))  # type: ignore
        current_frozen = Decimal(str(balance.frozen_amount))  # type: ignore
        
        new_amount = current_amount + amount_change
        new_frozen = current_frozen + freeze_change
        
        # 충분한 자금 확인
        if new_amount < 0 or new_frozen < 0:
            return None
        
        # 사용 가능한 잔액이 충분한지 확인
        available_balance = current_amount - current_frozen
        if amount_change < 0 and abs(amount_change) > available_balance:
            return None
        
        # SQLAlchemy 타입 이슈를 피하기 위해 쿼리를 사용하여 업데이트
        db.query(models.Balance).filter(models.Balance.id == balance.id).update({
            'amount': new_amount,
            'frozen_amount': new_frozen,
            'updated_at': datetime.utcnow()
        })
        
        db.commit()
        db.refresh(balance)
        return balance
    
    def freeze_amount(self, db: Session, user_id: int, asset: str, amount: Decimal) -> bool:
        """Freeze specific amount for withdrawal processing."""
        balance = self.get_user_balance(db, user_id, asset)
        if not balance:
            return False
        
        current_amount = Decimal(str(balance.amount))  # type: ignore
        current_frozen = Decimal(str(balance.frozen_amount))  # type: ignore
        available = current_amount - current_frozen
        
        if available < amount:
            return False
        
        db.query(models.Balance).filter(models.Balance.id == balance.id).update({
            'frozen_amount': current_frozen + amount
        })
        db.commit()
        return True
    
    def unfreeze_amount(self, db: Session, user_id: int, asset: str, amount: Decimal) -> bool:
        """Unfreeze specific amount."""
        balance = self.get_user_balance(db, user_id, asset)
        if not balance:
            return False
            
        current_frozen = Decimal(str(balance.frozen_amount))  # type: ignore
        if current_frozen < amount:
            return False
        
        db.query(models.Balance).filter(models.Balance.id == balance.id).update({
            'frozen_amount': current_frozen - amount
        })
        db.commit()
        return True


class CRUDTransaction:
    """CRUD operations for Transaction model."""
    
    def create(self, db: Session, transaction_data: dict) -> models.Transaction:
        """Create new transaction record."""
        db_transaction = models.Transaction(**transaction_data)
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction
    
    def get(self, db: Session, transaction_id: int) -> Optional[models.Transaction]:
        """Get transaction by ID."""
        return db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    
    def get_user_transactions(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20,
        transaction_type: Optional[models.TransactionType] = None
    ) -> List[models.Transaction]:
        """Get user transactions with pagination and filtering."""
        query = db.query(models.Transaction).filter(models.Transaction.user_id == user_id)
        
        if transaction_type:
            query = query.filter(models.Transaction.type == transaction_type)
        
        return query.order_by(desc(models.Transaction.created_at)).offset(skip).limit(limit).all()
    
    def update_status(
        self, 
        db: Session, 
        transaction_id: int, 
        status: models.TransactionStatus,
        ref_tx_id: Optional[str] = None
    ) -> Optional[models.Transaction]:
        """Update transaction status."""
        transaction = self.get(db, transaction_id)
        if not transaction:
            return None
        
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        if ref_tx_id:
            update_data['ref_tx_id'] = ref_tx_id
        
        db.query(models.Transaction).filter(models.Transaction.id == transaction_id).update(update_data)
        db.commit()
        db.refresh(transaction)
        return transaction
    
    def create_internal_transfer(
        self,
        db: Session,
        sender_id: int,
        recipient_id: int,
        amount: Decimal,
        asset: str = "USDT",
        memo: Optional[str] = None
    ) -> Optional[models.Transaction]:
        """
        Create internal transfer transaction atomically.
        
        This involves:
        1. Deducting from sender balance
        2. Adding to recipient balance
        3. Creating transaction records
        """
        try:
            # 발송자 잔액 확인
            sender_balance = crud_balance.get_user_balance(db, sender_id, asset)
            if not sender_balance:
                return None
                
            current_amount = Decimal(str(sender_balance.amount))  # type: ignore
            current_frozen = Decimal(str(sender_balance.frozen_amount))  # type: ignore
            available = current_amount - current_frozen
            
            if available < amount:
                return None
            
            # 잔액 업데이트
            sender_updated = crud_balance.update_balance(db, sender_id, asset, -amount)
            recipient_updated = crud_balance.update_balance(db, recipient_id, asset, amount)
            
            if not sender_updated or not recipient_updated:
                db.rollback()
                return None
            
            # 트랜잭션 기록 생성
            transaction_data = {
                "user_id": sender_id,
                "type": models.TransactionType.TRANSFER,
                "amount": amount,
                "asset": asset,
                "status": models.TransactionStatus.COMPLETED,
                "related_user_id": recipient_id,
                "memo": memo,
                "fee_amount": Decimal('0.00000000')
            }
            
            transaction = self.create(db, transaction_data)
            return transaction
            
        except Exception as e:
            db.rollback()
            raise e


class CRUDWithdrawalRequest:
    """CRUD operations for WithdrawalRequest model."""
    
    def create(
        self,
        db: Session,
        user_id: int,
        amount: Decimal,
        destination_address: str,
        asset: str = "USDT",
        memo: Optional[str] = None
    ) -> Optional[models.WithdrawalRequest]:
        """Create withdrawal request and freeze funds."""
        try:
            # 출금 금액 동결
            success = crud_balance.freeze_amount(db, user_id, asset, amount)
            if not success:
                return None
            
            # 출금 요청 생성
            withdrawal_request = models.WithdrawalRequest(
                user_id=user_id,
                amount=amount,
                asset=asset,
                destination_address=destination_address,
                status=models.TransactionStatus.PENDING,
                memo=memo
            )
            
            db.add(withdrawal_request)
            db.commit()
            db.refresh(withdrawal_request)
            
            return withdrawal_request
            
        except Exception as e:
            db.rollback()
            raise e
    
    def get_pending_requests(self, db: Session, skip: int = 0, limit: int = 50) -> List[models.WithdrawalRequest]:
        """Get pending withdrawal requests for admin review."""
        return db.query(models.WithdrawalRequest).filter(
            models.WithdrawalRequest.status == models.TransactionStatus.PENDING
        ).order_by(desc(models.WithdrawalRequest.created_at)).offset(skip).limit(limit).all()
    
    def approve_request(
        self,
        db: Session,
        request_id: int,
        admin_user_id: int,
        approved: bool,
        admin_memo: Optional[str] = None
    ) -> Optional[models.WithdrawalRequest]:
        """Approve or reject withdrawal request."""
        withdrawal_request = db.query(models.WithdrawalRequest).filter(
            models.WithdrawalRequest.id == request_id
        ).first()
        
        if not withdrawal_request:
            return None
        
        update_data = {
            'admin_user_id': admin_user_id,
            'processed_at': datetime.utcnow()
        }
        
        if approved:
            update_data['status'] = models.TransactionStatus.COMPLETED
        else:
            update_data['status'] = models.TransactionStatus.CANCELLED
            # Unfreeze the amount if rejected
            crud_balance.unfreeze_amount(
                db, 
                int(withdrawal_request.user_id),  # type: ignore
                str(withdrawal_request.asset),  # type: ignore
                Decimal(str(withdrawal_request.amount))  # type: ignore
            )
        
        if admin_memo:
            update_data['memo'] = admin_memo
        
        db.query(models.WithdrawalRequest).filter(
            models.WithdrawalRequest.id == request_id
        ).update(update_data)
        
        db.commit()
        db.refresh(withdrawal_request)
        
        return withdrawal_request


# Global CRUD instances
crud_user = CRUDUser()
crud_balance = CRUDBalance()
crud_transaction = CRUDTransaction()
crud_withdrawal_request = CRUDWithdrawalRequest()
