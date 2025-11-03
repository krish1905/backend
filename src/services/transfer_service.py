"""P2P Transfer service with atomic transactions."""
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from uuid import UUID
from typing import Optional

from ..models import User, Transaction, TransactionStatus, TransactionCategory
from ..config import settings


class TransferService:
    """Service for handling P2P transfers."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_money(
        self,
        from_user: User,
        to_user_email: str,
        amount: Decimal,
        description: Optional[str] = None
    ) -> Transaction:
        """
        Execute a P2P transfer from one user to another.
        
        This operation is atomic - either both balance updates succeed or both fail.
        
        Args:
            from_user: The sender user object
            to_user_email: Email of the recipient
            amount: Amount to transfer
            description: Optional description
            
        Returns:
            Created transaction object
            
        Raises:
            HTTPException: If validation fails or transaction fails
        """
        # Validate amount
        amount = Decimal(str(amount)).quantize(Decimal('0.01'))
        
        if amount < settings.min_transfer_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum transfer amount is ${settings.min_transfer_amount}"
            )
        
        if amount > settings.max_transfer_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum transfer amount is ${settings.max_transfer_amount}"
            )
        
        # Find recipient
        to_user = self.db.query(User).filter(User.email == to_user_email).first()
        if not to_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {to_user_email} not found"
            )
        
        # Prevent self-transfer
        if from_user.id == to_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer money to yourself"
            )
        
        # Check sufficient balance
        if from_user.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Current balance: ${from_user.balance}"
            )
        
        try:
            # Begin atomic transaction
            # Create transaction record first (in pending state)
            transaction = Transaction(
                from_user_id=from_user.id,
                to_user_id=to_user.id,
                amount=amount,
                description=description,
                status=TransactionStatus.PENDING,
                category=TransactionCategory.TRANSFER
            )
            self.db.add(transaction)
            self.db.flush()  # Get transaction ID without committing
            
            # Update balances atomically
            from_user.balance -= amount
            to_user.balance += amount
            
            # Mark transaction as completed
            transaction.status = TransactionStatus.COMPLETED
            
            # Commit all changes together (atomic)
            self.db.commit()
            self.db.refresh(transaction)
            
            return transaction
            
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during transfer: {str(e)}"
            )
        except Exception as e:
            self.db.rollback()
            # Mark transaction as failed if it was created
            if transaction and transaction.id:
                transaction.status = TransactionStatus.FAILED
                try:
                    self.db.commit()
                except:
                    pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transfer failed: {str(e)}"
            )
    
    def get_user_transactions(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        transaction_type: Optional[str] = None  # 'sent', 'received', or None for all
    ) -> tuple[list[Transaction], int]:
        """
        Get transactions for a user.
        
        Args:
            user_id: User UUID
            limit: Number of transactions to return
            offset: Number of transactions to skip
            transaction_type: Filter by 'sent', 'received', or None for all
            
        Returns:
            Tuple of (transactions list, total count)
        """
        query = self.db.query(Transaction)
        
        if transaction_type == 'sent':
            query = query.filter(Transaction.from_user_id == user_id)
        elif transaction_type == 'received':
            query = query.filter(Transaction.to_user_id == user_id)
        else:
            # All transactions (sent or received)
            query = query.filter(
                (Transaction.from_user_id == user_id) | 
                (Transaction.to_user_id == user_id)
            )
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        transactions = (
            query
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        return transactions, total
    
    def get_transaction_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get a transaction by ID."""
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    def search_users(self, email: str, current_user_id: UUID) -> list[User]:
        """
        Search for users by email (for transfer recipient selection).
        
        Args:
            email: Email search string
            current_user_id: Current user's ID (to exclude from results)
            
        Returns:
            List of matching users
        """
        return (
            self.db.query(User)
            .filter(
                User.email.ilike(f"%{email}%"),
                User.id != current_user_id  # Exclude current user
            )
            .limit(10)
            .all()
        )

