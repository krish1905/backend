"""Supabase authentication and JWT verification."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional
from supabase import create_client, Client
import logging

from .config import settings
from .database import get_db
from .models import User

logger = logging.getLogger(__name__)

# Supabase client (with configuration check)
if settings.is_configured:
    supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    logger.info("Supabase client initialized successfully")
else:
    logger.warning("Supabase not configured - using placeholder client")
    # Create a placeholder that will raise errors if used
    class PlaceholderSupabaseClient:
        def __getattr__(self, name):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not configured. Please set up .env file with Supabase credentials."
            )
    supabase = PlaceholderSupabaseClient()  # type: ignore

# Security scheme for JWT tokens
security = HTTPBearer()


def get_supabase_client() -> Client:
    """Get Supabase client."""
    return supabase


async def verify_token(token: str) -> dict:
    """
    Verify Supabase JWT token.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Verify the token with Supabase
        response = supabase.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "sub": str(response.user.id),
            "email": response.user.email,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If user not found or token invalid
    """
    token = credentials.credentials
    
    # Verify token and get user info
    token_data = await verify_token(token)
    user_id = token_data.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# Helper functions for Supabase auth operations
async def sign_up_user(email: str, password: str, full_name: Optional[str] = None) -> dict:
    """
    Register a new user with Supabase.
    
    Args:
        email: User email
        password: User password
        full_name: Optional full name
        
    Returns:
        User data and session info
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Sign up with Supabase
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed"
            )
        
        return {
            "user": response.user,
            "session": response.session
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


async def sign_in_user(email: str, password: str) -> dict:
    """
    Sign in a user with Supabase.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User data and session info with access token
        
    Raises:
        HTTPException: If login fails
    """
    try:
        # Sign in with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        return {
            "user": response.user,
            "session": response.session,
            "access_token": response.session.access_token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )


async def sign_out_user(token: str) -> bool:
    """
    Sign out a user.
    
    Args:
        token: JWT access token
        
    Returns:
        True if successful
    """
    try:
        supabase.auth.sign_out()
        return True
    except Exception:
        return False

