"""
Transaction-related API routes.
Handles transaction history, withdrawal requests, and transaction status.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from ..core.db import get_db
from ..core.config import settings
from ..crud import crud_transaction, crud_withdrawal_request, crud_balance
from ..deps import get_current_active_user, common_pagination_params
from ..utils.tron import get_tron_service
from .. import schemas, models

router = APIRouter()


@router.get("/transactions", response_model=schemas.TransactionHistory)
def get_transaction_history(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    pagination: dict = Depends(common_pagination_params),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    asset: Optional[str] = Query(None, description="Filter by asset")
) -> Any:
    """
    Get user transaction history with pagination and filtering.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **transaction_type**: Filter by type (deposit, withdrawal, transfer, payment)
    - **asset**: Filter by asset (e.g., USDT)
    
    Returns paginated list of user transactions.
    """
    try:
        # Parse transaction type if provided
        tx_type_filter = None
        if transaction_type:
            try:
                tx_type_filter = models.TransactionType(transaction_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid transaction type: {transaction_type}"
                )
        
        # Get transactions
        transactions = crud_transaction.get_user_transactions(
            db=db,
            user_id=int(current_user.id),  # type: ignore
            skip=pagination["skip"],
            limit=pagination["limit"],
            transaction_type=tx_type_filter
        )
        
        # Convert to response format
        transaction_responses = []
        for tx in transactions:
            # Filter by asset if specified
            if asset and str(tx.asset) != asset:  # type: ignore
                continue
                
            transaction_responses.append(
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
            )
        
        return schemas.TransactionHistory(
            transactions=transaction_responses,
            total_count=len(transaction_responses),
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transaction history: {str(e)}"
        )


@router.get("/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def get_transaction_detail(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    transaction_id: int
) -> Any:
    """
    Get detailed information for a specific transaction.
    
    - **transaction_id**: Transaction ID to retrieve
    
    Returns detailed transaction information.
    """
    try:
        transaction = crud_transaction.get(db, transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if user owns this transaction
        if int(transaction.user_id) != int(current_user.id):  # type: ignore
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return schemas.TransactionResponse(
            id=int(transaction.id),  # type: ignore
            user_id=int(transaction.user_id),  # type: ignore
            type=transaction.type,  # type: ignore
            amount=Decimal(str(transaction.amount)),  # type: ignore
            asset=str(transaction.asset),  # type: ignore
            status=transaction.status,  # type: ignore
            ref_tx_id=str(transaction.ref_tx_id) if transaction.ref_tx_id else None,  # type: ignore
            related_user_id=int(transaction.related_user_id) if transaction.related_user_id else None,  # type: ignore
            memo=str(transaction.memo) if transaction.memo else None,  # type: ignore
            fee_amount=Decimal(str(transaction.fee_amount)),  # type: ignore
            created_at=transaction.created_at,  # type: ignore
            updated_at=transaction.updated_at  # type: ignore
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transaction: {str(e)}"
        )


@router.post("/withdraw", response_model=schemas.WithdrawalResponse)
def create_withdrawal_request(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    withdrawal_data: schemas.WithdrawalRequest
) -> Any:
    """
    Create a withdrawal request.
    
    - **amount**: Withdrawal amount (must be positive and within limits)
    - **asset**: Asset to withdraw (default: USDT)
    - **destination_address**: Valid Tron address for receiving funds
    - **memo**: Optional withdrawal memo
    
    Withdrawal requests require admin approval before processing.
    """
    try:
        # Validate withdrawal amount limits
        if withdrawal_data.amount < Decimal(str(settings.min_withdrawal_amount)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum withdrawal amount is {settings.min_withdrawal_amount} {withdrawal_data.asset}"
            )
        
        if withdrawal_data.amount > Decimal(str(settings.max_withdrawal_amount)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum withdrawal amount is {settings.max_withdrawal_amount} {withdrawal_data.asset}"
            )
        
        # Validate Tron address
        if not get_tron_service().is_valid_address(withdrawal_data.destination_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Tron address format"
            )
        
        # Check user balance
        user_balance = crud_balance.get_user_balance(
            db, int(current_user.id), withdrawal_data.asset  # type: ignore
        )
        if not user_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No {withdrawal_data.asset} balance found"
            )
        
        current_amount = Decimal(str(user_balance.amount))  # type: ignore
        current_frozen = Decimal(str(user_balance.frozen_amount))  # type: ignore
        available_balance = current_amount - current_frozen
        
        # Calculate withdrawal fee
        fee_amount = withdrawal_data.amount * Decimal(str(settings.withdrawal_fee_percentage))
        total_amount = withdrawal_data.amount + fee_amount
        
        if available_balance < total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Available: {available_balance}, Required: {total_amount} (including fee: {fee_amount})"
            )
        
        # Create withdrawal request
        withdrawal_request = crud_withdrawal_request.create(
            db=db,
            user_id=int(current_user.id),  # type: ignore
            amount=withdrawal_data.amount,
            destination_address=withdrawal_data.destination_address,
            asset=withdrawal_data.asset,
            memo=withdrawal_data.memo
        )
        
        if not withdrawal_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create withdrawal request"
            )
        
        return schemas.WithdrawalResponse(
            request_id=int(withdrawal_request.id),  # type: ignore
            status="pending",
            message="Withdrawal request created and pending admin approval",
            estimated_fee=fee_amount
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create withdrawal request: {str(e)}"
        )


@router.get("/withdraw/requests", response_model=List[dict])
def get_user_withdrawal_requests(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    pagination: dict = Depends(common_pagination_params)
) -> Any:
    """
    Get user's withdrawal requests.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20)
    
    Returns list of user's withdrawal requests.
    """
    try:
        # Note: This would require adding a method to crud_withdrawal_request
        # to get user-specific requests. For now, return empty list.
        return []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve withdrawal requests: {str(e)}"
        )


@router.get("/status/{tx_hash}")
def check_transaction_status(
    tx_hash: str,
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Check blockchain transaction status.
    
    - **tx_hash**: Transaction hash to check
    
    Returns transaction status and confirmation information.
    """
    try:
        if not tx_hash or len(tx_hash) != 64:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction hash format"
            )
        
        # Check transaction status on blockchain
        status_info = get_tron_service().check_transaction_status(tx_hash)
        
        return {
            "tx_hash": tx_hash,
            "status": status_info,
            "message": "Transaction status retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check transaction status: {str(e)}"
        )
