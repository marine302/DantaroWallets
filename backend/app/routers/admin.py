"""
Admin-related API routes.
Handles admin functions like user management, withdrawal approvals, and system monitoring.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from ..core.db import get_db
from ..core.config import settings
from ..crud import crud_user, crud_balance, crud_withdrawal_request, crud_transaction
from ..deps import get_current_admin_user, common_pagination_params
from ..utils.tron import get_tron_service
from .. import schemas, models

router = APIRouter()


@router.get("/users", response_model=schemas.AdminUserList)
def get_all_users(
    *,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
    pagination: dict = Depends(common_pagination_params)
) -> Any:
    """
    Get all users in the system (admin only).
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20)
    
    Returns paginated list of all users.
    """
    try:
        users = crud_user.get_multi(
            db, skip=pagination["skip"], limit=pagination["limit"]
        )
        
        user_responses = [
            schemas.UserResponse(
                id=int(user.id),  # type: ignore
                email=str(user.email),  # type: ignore
                is_admin=bool(user.is_admin),  # type: ignore
                is_active=bool(user.is_active),  # type: ignore
                created_at=user.created_at  # type: ignore
            )
            for user in users
        ]
        
        return schemas.AdminUserList(
            users=user_responses,
            total_count=len(user_responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/balances", response_model=List[schemas.AdminBalanceView])
def get_all_balances(
    *,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
    pagination: dict = Depends(common_pagination_params),
    user_email: str = Query(None, description="Filter by user email")
) -> Any:
    """
    Get balance overview for all users (admin only).
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20)
    - **user_email**: Optional filter by user email
    
    Returns balance information for all users.
    """
    try:
        balance_views = []
        
        if user_email:
            # Get specific user
            user = crud_user.get_by_email(db, email=user_email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            users = [user]
        else:
            # Get all users
            users = crud_user.get_multi(
                db, skip=pagination["skip"], limit=pagination["limit"]
            )
        
        for user in users:
            balances = crud_balance.get_user_balances(db, int(user.id))  # type: ignore
            
            balance_responses = [
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
            
            # Calculate total USD value (simplified - in production use real exchange rates)
            total_balance_usd = sum(
                balance.amount for balance in balance_responses 
                if balance.asset == "USDT"
            ) or Decimal('0')
            
            balance_views.append(
                schemas.AdminBalanceView(
                    user_id=int(user.id),  # type: ignore
                    user_email=str(user.email),  # type: ignore
                    balances=balance_responses,
                    total_balance_usd=total_balance_usd
                )
            )
        
        return balance_views
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve balances: {str(e)}"
        )


@router.get("/withdrawals/pending", response_model=schemas.AdminWithdrawalList)
def get_pending_withdrawals(
    *,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
    pagination: dict = Depends(common_pagination_params)
) -> Any:
    """
    Get pending withdrawal requests for admin approval.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50)
    
    Returns list of pending withdrawal requests.
    """
    try:
        pending_requests = crud_withdrawal_request.get_pending_requests(
            db, skip=pagination["skip"], limit=pagination["limit"]
        )
        
        requests_data = []
        for request in pending_requests:
            # Get user info
            user = crud_user.get(db, int(request.user_id))  # type: ignore
            
            requests_data.append({
                "id": int(request.id),  # type: ignore
                "user_id": int(request.user_id),  # type: ignore
                "user_email": str(user.email) if user else "Unknown",  # type: ignore
                "amount": float(request.amount),  # type: ignore
                "asset": str(request.asset),  # type: ignore
                "destination_address": str(request.destination_address),  # type: ignore
                "status": str(request.status),  # type: ignore
                "memo": str(request.memo) if request.memo else None,  # type: ignore
                "created_at": request.created_at.isoformat() if request.created_at else None,  # type: ignore
            })
        
        return schemas.AdminWithdrawalList(
            requests=requests_data,
            total_count=len(requests_data)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pending withdrawals: {str(e)}"
        )


@router.post("/withdrawals/approve", response_model=schemas.SuccessResponse)
def approve_withdrawal_request(
    *,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
    approval_data: schemas.WithdrawalApproval
) -> Any:
    """
    Approve or reject a withdrawal request.
    
    - **request_id**: Withdrawal request ID
    - **approved**: True to approve, False to reject
    - **admin_memo**: Optional admin memo/reason
    
    Approved requests will trigger blockchain transaction.
    """
    try:
        # Process approval
        updated_request = crud_withdrawal_request.approve_request(
            db=db,
            request_id=approval_data.request_id,
            admin_user_id=int(current_admin.id),  # type: ignore
            approved=approval_data.approved,
            admin_memo=approval_data.admin_memo
        )
        
        if not updated_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Withdrawal request not found"
            )
        
        if approval_data.approved:
            # If approved, initiate blockchain transaction
            # This would typically be done in a background task
            try:
                tx_hash = get_tron_service().send_usdt(
                    to_address=str(updated_request.destination_address),  # type: ignore
                    amount=Decimal(str(updated_request.amount)),  # type: ignore
                    memo=approval_data.admin_memo
                )
                
                if tx_hash:
                    # Create transaction record
                    transaction_data = {
                        "user_id": int(updated_request.user_id),  # type: ignore
                        "type": models.TransactionType.WITHDRAWAL,
                        "amount": Decimal(str(updated_request.amount)),  # type: ignore
                        "asset": str(updated_request.asset),  # type: ignore
                        "status": models.TransactionStatus.COMPLETED,
                        "ref_tx_id": tx_hash,
                        "memo": approval_data.admin_memo,
                        "fee_amount": Decimal('0.00000000')  # Fee already deducted
                    }
                    
                    crud_transaction.create(db, transaction_data)
                    
                    return schemas.SuccessResponse(
                        message=f"Withdrawal approved and blockchain transaction initiated: {tx_hash}",
                        data={"tx_hash": tx_hash, "request_id": approval_data.request_id}
                    )
                else:
                    return schemas.SuccessResponse(
                        message="Withdrawal approved but blockchain transaction failed. Manual intervention required.",
                        data={"request_id": approval_data.request_id}
                    )
                    
            except Exception as blockchain_error:
                # Log the error but don't fail the approval
                return schemas.SuccessResponse(
                    message=f"Withdrawal approved but blockchain error occurred: {str(blockchain_error)}",
                    data={"request_id": approval_data.request_id}
                )
        else:
            return schemas.SuccessResponse(
                message="Withdrawal request rejected and funds unfrozen",
                data={"request_id": approval_data.request_id}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process withdrawal approval: {str(e)}"
        )


@router.post("/send", response_model=schemas.SuccessResponse)
def admin_send_transaction(
    *,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
    send_data: schemas.AdminSendTransaction
) -> Any:
    """
    Admin-initiated blockchain transaction (admin only).
    
    - **to_address**: Destination Tron address
    - **amount**: Amount to send
    - **asset**: Asset to send (default: USDT)
    - **memo**: Optional transaction memo
    
    Direct blockchain transaction bypassing normal user flow.
    """
    try:
        # Validate address
        if not get_tron_service().is_valid_address(send_data.to_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Tron address format"
            )
        
        # Check company wallet balance
        company_balance = get_tron_service().get_account_balance(get_tron_service().company_address)
        
        if send_data.asset == "USDT":
            available_balance = company_balance.get("USDT", Decimal('0'))
        else:
            available_balance = company_balance.get("TRX", Decimal('0'))
        
        if available_balance < send_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient company wallet balance. Available: {available_balance} {send_data.asset}"
            )
        
        # Send transaction
        if send_data.asset == "USDT":
            tx_hash = get_tron_service().send_usdt(
                to_address=send_data.to_address,
                amount=send_data.amount,
                memo=send_data.memo
            )
        else:
            # For TRX or other assets, implement separate sending logic
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sending {send_data.asset} not implemented yet"
            )
        
        if not tx_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Blockchain transaction failed"
            )
        
        # Create transaction record (system transaction)
        transaction_data = {
            "user_id": int(current_admin.id),  # type: ignore
            "type": models.TransactionType.WITHDRAWAL,  # Admin withdrawal
            "amount": send_data.amount,
            "asset": send_data.asset,
            "status": models.TransactionStatus.COMPLETED,
            "ref_tx_id": tx_hash,
            "memo": f"Admin send: {send_data.memo}" if send_data.memo else "Admin send",
            "fee_amount": Decimal('0.00000000')
        }
        
        transaction = crud_transaction.create(db, transaction_data)
        
        return schemas.SuccessResponse(
            message="Admin transaction sent successfully",
            data={
                "tx_hash": tx_hash,
                "transaction_id": int(transaction.id),  # type: ignore
                "amount": float(send_data.amount),
                "to_address": send_data.to_address
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send admin transaction: {str(e)}"
        )


@router.get("/system/status")
def get_system_status(
    current_admin: models.User = Depends(get_current_admin_user)
) -> Any:
    """
    Get system status information (admin only).
    
    Returns various system metrics and status information.
    """
    try:
        # Get company wallet balance
        company_balance = get_tron_service().get_account_balance(get_tron_service().company_address)
        
        return {
            "system_status": "operational",
            "company_wallet": {
                "address": get_tron_service().company_address,
                "balances": {
                    "TRX": float(company_balance.get("TRX", Decimal('0'))),
                    "USDT": float(company_balance.get("USDT", Decimal('0')))
                }
            },
            "tron_network": settings.tron_network,
            "deposit_monitoring": "active",
            "withdrawal_processing": "manual_approval",
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )


# Add time import at the top
import time
