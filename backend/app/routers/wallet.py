"""
지갑 관련 API 라우터.
잔액 조회, 내부 이체, 입금 작업을 처리합니다.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from ..core.db import get_db
from ..crud import crud_balance, crud_user, crud_transaction
from ..deps import get_current_active_user, common_pagination_params
from ..utils.tron import get_tron_service
from .. import schemas, models

router = APIRouter()


@router.get("/balance", response_model=List[schemas.BalanceResponse])
def get_user_balance(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    asset: str = Query(None, description="조회할 특정 자산 (예: 'USDT')")
) -> Any:
    """
    모든 자산 또는 특정 자산의 사용자 잔액 조회.
    
    - **asset**: 선택적 자산 필터 (기본값은 모든 자산)
    
    사용자 잔액 목록을 반환합니다.
    """
    try:
        if asset:
            # Get balance for specific asset
            balance = crud_balance.get_user_balance(db, int(current_user.id), asset)  # type: ignore
            if not balance:
                # Return zero balance if not found
                return [{
                    "id": 0,
                    "user_id": int(current_user.id),  # type: ignore
                    "asset": asset,
                    "amount": Decimal('0.00000000'),
                    "frozen_amount": Decimal('0.00000000'),
                    "updated_at": None
                }]
            return [schemas.BalanceResponse(
                id=int(balance.id),  # type: ignore
                user_id=int(balance.user_id),  # type: ignore
                asset=str(balance.asset),  # type: ignore
                amount=Decimal(str(balance.amount)),  # type: ignore
                frozen_amount=Decimal(str(balance.frozen_amount)),  # type: ignore
                updated_at=balance.updated_at  # type: ignore
            )]
        else:
            # Get all balances
            balances = crud_balance.get_user_balances(db, int(current_user.id))  # type: ignore
            return [
                schemas.BalanceResponse(
                    id=int(balance.id),  # type: ignore
                    user_id=int(balance.user_id),  # type: ignore
                    asset=str(balance.asset),  # type: ignore
                    amount=Decimal(str(balance.amount)),  # type: ignore
                    frozen_amount=Decimal(str(balance.frozen_amount)),  # type: ignore
                    updated_at=balance.updated_at  # type: ignore
                )
                for balance in balances
            ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve balance: {str(e)}"
        )


@router.post("/transfer", response_model=schemas.TransferResponse)
def create_internal_transfer(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    transfer_data: schemas.InternalTransfer
) -> Any:
    """
    Create internal transfer between users.
    
    - **recipient_email**: Email of the recipient user
    - **amount**: Transfer amount (must be positive)
    - **asset**: Asset to transfer (default: USDT)
    - **memo**: Optional transfer memo
    
    Transfers are instant and have no fees.
    """
    # Validate recipient
    recipient = crud_user.get_by_email(db, email=transfer_data.recipient_email)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found"
        )
    
    if int(recipient.id) == int(current_user.id):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to yourself"
        )
    
    if not crud_user.is_active(recipient):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient user is inactive"
        )
    
    # Check sender balance
    sender_balance = crud_balance.get_user_balance(
        db, int(current_user.id), transfer_data.asset  # type: ignore
    )
    if not sender_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No {transfer_data.asset} balance found"
        )
    
    current_amount = Decimal(str(sender_balance.amount))  # type: ignore
    current_frozen = Decimal(str(sender_balance.frozen_amount))  # type: ignore
    available_balance = current_amount - current_frozen
    
    if available_balance < transfer_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    try:
        # Create transfer transaction
        transaction = crud_transaction.create_internal_transfer(
            db=db,
            sender_id=int(current_user.id),  # type: ignore
            recipient_id=int(recipient.id),  # type: ignore
            amount=transfer_data.amount,
            asset=transfer_data.asset,
            memo=transfer_data.memo
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer failed due to insufficient funds or system error"
            )
        
        return schemas.TransferResponse(
            transaction_id=int(transaction.id),  # type: ignore
            status="completed",
            message="Transfer completed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer failed: {str(e)}"
        )


@router.get("/deposit/address", response_model=schemas.DepositAddress)
def get_deposit_address(
    *,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get deposit address for receiving USDT.
    
    Returns the company wallet address where users can send USDT.
    For deposit identification, users should include their user ID as memo.
    """
    try:
        user_id = int(current_user.id)  # type: ignore
        company_address = get_tron_service().company_address
        
        if not company_address:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Deposit service temporarily unavailable"
            )
        
        return schemas.DepositAddress(
            address=company_address,
            memo=str(user_id),  # User ID as memo for identification
            qr_code=None  # Could generate QR code here
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deposit address: {str(e)}"
        )


@router.post("/deposit/check", response_model=schemas.DepositCheck)
def check_deposits(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Manually check for deposits (useful for testing).
    
    In production, deposits are automatically detected by the monitoring service.
    This endpoint allows users to manually trigger a deposit check.
    """
    try:
        # Get recent transactions for the user
        user_transactions = crud_transaction.get_user_transactions(
            db=db,
            user_id=int(current_user.id),  # type: ignore
            transaction_type=models.TransactionType.DEPOSIT,
            limit=10
        )
        
        # Convert to response format
        found_deposits = [
            schemas.TransactionResponse(
                id=int(tx.id),  # type: ignore
                user_id=int(tx.user_id),  # type: ignore
                type=tx.type,  # type: ignore
                amount=Decimal(str(tx.amount)),  # type: ignore
                asset=str(tx.asset),  # type: ignore
                status=tx.status,  # type: ignore
                ref_tx_id=str(tx.ref_tx_id) if tx.ref_tx_id else None,  # type: ignore
                related_user_id=int(tx.related_user_id) if tx.related_user_id else None,  # type: ignore
                memo=str(tx.memo) if tx.memo else None,  # type: ignore
                fee_amount=Decimal(str(tx.fee_amount)),  # type: ignore
                created_at=tx.created_at,  # type: ignore
                updated_at=tx.updated_at  # type: ignore
            )
            for tx in user_transactions
        ]
        
        return schemas.DepositCheck(
            found_deposits=found_deposits,
            message=f"Found {len(found_deposits)} recent deposits"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check deposits: {str(e)}"
        )


@router.get("/address/validate")
def validate_tron_address(
    address: str = Query(..., description="Tron address to validate")
) -> Any:
    """
    Validate Tron address format.
    
    - **address**: Tron address string to validate
    
    Returns validation result.
    """
    try:
        is_valid = get_tron_service().is_valid_address(address)
        
        return {
            "address": address,
            "is_valid": is_valid,
            "message": "Valid Tron address" if is_valid else "Invalid Tron address format"
        }
        
    except Exception as e:
        return {
            "address": address,
            "is_valid": False,
            "message": f"Validation error: {str(e)}"
        }
