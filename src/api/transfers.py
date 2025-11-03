"""Transfer API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..models import User
from ..schemas import (
    TransferRequest, TransferResponse, TransactionResponse,
    TransactionListResponse, UserSearchResponse, TransactionDetailResponse
)
from ..config import settings
from ..services.transfer_service import TransferService

# Import appropriate auth based on configuration
if settings.is_configured:
    from ..auth import get_current_user
else:
    from ..auth_local import get_current_user_local as get_current_user

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def send_money(
    transfer_request: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send money to another user (P2P transfer).
    
    Validates the transfer amount, checks sender's balance, and executes
    an atomic transaction to update both users' balances.
    """
    transfer_service = TransferService(db)
    
    try:
        transaction = transfer_service.send_money(
            from_user=current_user,
            to_user_email=transfer_request.to_user_email,
            amount=transfer_request.amount,
            description=transfer_request.description
        )
        
        # Prepare response
        transaction_response = TransactionResponse(
            id=transaction.id,
            from_user_id=transaction.from_user_id,
            to_user_id=transaction.to_user_id,
            amount=transaction.amount,
            description=transaction.description,
            status=transaction.status,
            category=transaction.category,
            created_at=transaction.created_at,
            sender_email=current_user.email,
            receiver_email=transfer_request.to_user_email
        )
        
        return TransferResponse(
            success=True,
            transaction_id=transaction.id,
            message=f"Successfully sent ${transaction.amount} to {transfer_request.to_user_email}",
            transaction=transaction_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer failed: {str(e)}"
        )


@router.get("", response_model=TransactionListResponse)
async def get_transactions(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None, regex="^(sent|received|all)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's transaction history.
    
    Query parameters:
    - limit: Number of transactions to return (1-100, default 10)
    - offset: Number of transactions to skip (default 0)
    - type: Filter by 'sent', 'received', or 'all' (default all)
    """
    transfer_service = TransferService(db)
    
    # Map 'all' to None for the service method
    transaction_type = None if type == 'all' else type
    
    transactions, total = transfer_service.get_user_transactions(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        transaction_type=transaction_type
    )
    
    # Prepare response
    transaction_responses = []
    for txn in transactions:
        # Determine sender and receiver emails
        sender_email = current_user.email if txn.from_user_id == current_user.id else (txn.sender.email if txn.sender else None)
        receiver_email = current_user.email if txn.to_user_id == current_user.id else (txn.receiver.email if txn.receiver else None)
        
        transaction_responses.append(TransactionResponse(
            id=txn.id,
            from_user_id=txn.from_user_id,
            to_user_id=txn.to_user_id,
            amount=txn.amount,
            description=txn.description,
            status=txn.status,
            category=txn.category,
            created_at=txn.created_at,
            sender_email=sender_email,
            receiver_email=receiver_email
        ))
    
    return TransactionListResponse(
        total=total,
        limit=limit,
        offset=offset,
        transactions=transaction_responses
    )


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific transaction.
    
    User can only view transactions they are involved in (as sender or receiver).
    """
    transfer_service = TransferService(db)
    
    transaction = transfer_service.get_transaction_by_id(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Check if user is involved in the transaction
    if transaction.from_user_id != current_user.id and transaction.to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this transaction"
        )
    
    # Prepare detailed response with user info
    from ..schemas import UserResponse
    
    sender_response = None
    if transaction.sender:
        sender_response = UserResponse(
            id=transaction.sender.id,
            email=transaction.sender.email,
            full_name=transaction.sender.full_name,
            balance=transaction.sender.balance,
            created_at=transaction.sender.created_at,
            updated_at=transaction.sender.updated_at
        )
    
    receiver_response = None
    if transaction.receiver:
        receiver_response = UserResponse(
            id=transaction.receiver.id,
            email=transaction.receiver.email,
            full_name=transaction.receiver.full_name,
            balance=transaction.receiver.balance,
            created_at=transaction.receiver.created_at,
            updated_at=transaction.receiver.updated_at
        )
    
    return TransactionDetailResponse(
        id=transaction.id,
        from_user_id=transaction.from_user_id,
        to_user_id=transaction.to_user_id,
        amount=transaction.amount,
        description=transaction.description,
        status=transaction.status,
        category=transaction.category,
        created_at=transaction.created_at,
        sender_email=transaction.sender.email if transaction.sender else None,
        receiver_email=transaction.receiver.email if transaction.receiver else None,
        sender=sender_response,
        receiver=receiver_response
    )


@router.get("/users/search", response_model=List[UserSearchResponse])
async def search_users(
    email: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for users by email (for recipient selection).
    
    Returns a list of users matching the email search string.
    Excludes the current user from results.
    """
    transfer_service = TransferService(db)
    
    users = transfer_service.search_users(email, current_user.id)
    
    return [
        UserSearchResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name
        )
        for user in users
    ]

