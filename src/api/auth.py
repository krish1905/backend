"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserLogin, AuthResponse, UserResponse
from ..config import settings

# Import appropriate auth module based on configuration
if settings.is_configured:
    from ..auth import sign_up_user, sign_in_user, get_current_user
    USE_SUPABASE = True
else:
    from ..auth_local import (
        get_current_user_local as get_current_user,
        authenticate_user,
        get_password_hash,
        create_access_token
    )
    USE_SUPABASE = False

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    In development mode (no Supabase): Uses local JWT authentication.
    In production mode: Uses Supabase authentication.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if USE_SUPABASE:
        # Supabase mode
        auth_response = await sign_up_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        db_user = User(
            id=auth_response["user"].id,
            email=user_data.email,
            full_name=user_data.full_name,
            balance=1000.00
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        access_token = auth_response["session"].access_token
    else:
        # Local development mode
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            balance=1000.00
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(db_user.id)},
            expires_delta=timedelta(minutes=30)
        )
    
    user_response = UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        balance=db_user.balance,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    In development mode (no Supabase): Uses local JWT authentication.
    In production mode: Uses Supabase authentication.
    """
    if USE_SUPABASE:
        # Supabase mode
        auth_response = await sign_in_user(
            email=credentials.email,
            password=credentials.password
        )
        
        db_user = db.query(User).filter(User.id == auth_response["user"].id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database"
            )
        
        access_token = auth_response["access_token"]
    else:
        # Local development mode
        db_user = authenticate_user(db, credentials.email, credentials.password)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(db_user.id)},
            expires_delta=timedelta(minutes=30)
        )
    
    user_response = UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        balance=db_user.balance,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    
    Returns the authenticated user's profile information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        balance=current_user.balance,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.get("/balance", response_model=dict)
async def get_balance(current_user: User = Depends(get_current_user)):
    """
    Get current user's balance.
    
    Returns the authenticated user's current balance.
    """
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "balance": float(current_user.balance)
    }

