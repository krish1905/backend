"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from .models import TransactionStatus, TransactionCategory


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    balance: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserBalanceResponse(BaseModel):
    """Schema for balance response."""
    user_id: UUID
    email: str
    balance: Decimal
    
    class Config:
        from_attributes = True


# ============================================================================
# Authentication Schemas
# ============================================================================

class AuthResponse(BaseModel):
    """Schema for authentication response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token data."""
    sub: Optional[str] = None
    email: Optional[str] = None


# ============================================================================
# Transaction Schemas
# ============================================================================

class TransactionBase(BaseModel):
    """Base transaction schema."""
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: Optional[str] = Field(None, max_length=500)
    category: TransactionCategory = TransactionCategory.TRANSFER


class TransactionCreate(BaseModel):
    """Schema for creating a transaction (P2P transfer)."""
    to_user_email: EmailStr
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate transfer amount."""
        if v <= 0:
            raise ValueError('Amount must be greater than zero')
        if v > 10000:
            raise ValueError('Amount cannot exceed $10,000')
        return v


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: UUID
    from_user_id: UUID
    to_user_id: UUID
    status: TransactionStatus
    created_at: datetime
    
    # Optional nested user data
    sender_email: Optional[str] = None
    receiver_email: Optional[str] = None
    
    class Config:
        from_attributes = True


class TransactionDetailResponse(TransactionResponse):
    """Schema for detailed transaction response with user info."""
    sender: Optional[UserResponse] = None
    receiver: Optional[UserResponse] = None


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""
    total: int
    limit: int
    offset: int
    transactions: List[TransactionResponse]


# ============================================================================
# Transfer Schemas
# ============================================================================

class TransferRequest(BaseModel):
    """Schema for P2P transfer request."""
    to_user_email: EmailStr
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate transfer amount."""
        if v <= 0:
            raise ValueError('Amount must be greater than zero')
        if v < Decimal("0.01"):
            raise ValueError('Minimum transfer amount is $0.01')
        if v > Decimal("10000.00"):
            raise ValueError('Maximum transfer amount is $10,000')
        # Round to 2 decimal places
        return round(v, 2)


class TransferResponse(BaseModel):
    """Schema for transfer response."""
    success: bool
    transaction_id: UUID
    message: str
    transaction: TransactionResponse


# ============================================================================
# User Search Schemas
# ============================================================================

class UserSearchResponse(BaseModel):
    """Schema for user search response."""
    id: UUID
    email: str
    full_name: Optional[str]
    
    class Config:
        from_attributes = True


# ============================================================================
# Analytics Schemas
# ============================================================================

class BalanceHistoryPoint(BaseModel):
    """Schema for balance history data point."""
    date: datetime
    balance: Decimal


class SpendingByCategory(BaseModel):
    """Schema for spending by category."""
    category: str
    total_amount: Decimal
    transaction_count: int


class UserStats(BaseModel):
    """Schema for user statistics."""
    total_sent: Decimal
    total_received: Decimal
    transaction_count: int
    current_balance: Decimal


class MonthlyStats(BaseModel):
    """Schema for monthly statistics."""
    month: str
    total_sent: Decimal
    total_received: Decimal
    net_change: Decimal


# ============================================================================
# Error Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Schema for validation error response."""
    detail: List[dict]
    error_code: str = "validation_error"

