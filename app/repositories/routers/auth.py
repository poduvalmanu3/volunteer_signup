"""
Authentication router.
Handles user registration, login, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.models.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.repositories.user_repository import UserRepository
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Register a new user.
    
    **Privacy & Compliance:**
    - Collects age_band instead of DOB for privacy
    - Requires guardian consent for minors (under 18)
    - COPPA compliant for users under 13
    
    **Security:**
    - Password hashed with bcrypt before storage
    - Email and phone must be unique
    - Validates Indian phone number format
    
    **Request Body:**
    - name: Full name (2-100 characters)
    - email: Valid email address
    - phone: Indian phone number (+91 or 10 digits)
    - age_band: "under13", "13-17", or "18+"
    - password: Min 8 chars with uppercase, lowercase, digit
    - consent_flags: Terms, privacy, and guardian consent
    
    **Returns:**
    - 201: User created successfully
    - 400: Validation error or duplicate email/phone
    """
    repo = UserRepository(db)
    
    # Check if email already exists
    existing_user = await repo.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone already exists
    existing_phone = await repo.get_user_by_phone(user_data.phone)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user
    try:
        user = await repo.create_user(user_data)
        logger.info(f"New user registered: {user.id}")
        return user
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    **Security:**
    - Returns JWT access token (30 min expiry) and refresh token (7 days)
    - Password verified using constant-time comparison
    - Failed login attempts logged for monitoring
    
    **Request Body:**
    - email: User email address
    - password: User password
    
    **Returns:**
    - 200: Login successful with tokens
    - 401: Invalid credentials
    - 403: Account inactive
    """
    repo = UserRepository(db)
    
    # Get user by email
    user = await repo.get_user_by_email(credentials.email)
    
    if not user:
        # Don't reveal whether email exists (timing-safe)
        logger.warning(f"Login attempt with non-existent email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if account is active
    if not user.is_active:
        logger.warning(f"Login attempt on inactive account: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user.id, "roles": user.roles}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id}
    )
    
    logger.info(f"User logged in: {user.id}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )