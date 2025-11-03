"""Database models for Financial P2P Application."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
import uuid
import enum

from .database import Base, is_sqlite


# UUID type that works with both SQLite and PostgreSQL
if is_sqlite:
    # For SQLite, store UUID as string
    class UUID(TypeDecorator):
        """Platform-independent UUID type for SQLite."""
        impl = CHAR(36)
        cache_ok = True
        
        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            elif isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(value)
        
        def process_result_value(self, value, dialect):
            if value is None:
                return value
            return uuid.UUID(value)
else:
    # For PostgreSQL, use native UUID type
    UUID = PostgreSQL_UUID


class TransactionStatus(str, enum.Enum):
    """Transaction status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionCategory(str, enum.Enum):
    """Transaction category enum."""
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"


class User(Base):
    """User model - supports both Supabase and local auth."""
    __tablename__ = "users"
    
    # User ID (can be Supabase auth.users ID or local UUID)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # For local auth mode
    balance = Column(Numeric(10, 2), default=1000.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    sent_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.from_user_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.to_user_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, balance={self.balance})>"


class Transaction(Base):
    """Transaction model for P2P transfers."""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String, nullable=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    category = Column(SQLEnum(TransactionCategory), default=TransactionCategory.TRANSFER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    sender = relationship("User", foreign_keys=[from_user_id], back_populates="sent_transactions")
    receiver = relationship("User", foreign_keys=[to_user_id], back_populates="received_transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, from={self.from_user_id}, to={self.to_user_id}, amount={self.amount}, status={self.status})>"

