from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings


# Password hashing context using bcrypt (OWASP recommended)
# Bcrypt automatically handles salting and has built-in work factor
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password from user input
        hashed_password: The hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
        
    Security Notes:
        - Uses constant-time comparison to prevent timing attacks
        - Bcrypt handles salt automatically
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for secure storage.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password with salt
        
    Security Notes:
        - Uses bcrypt with automatic salting
        - Work factor automatically managed by passlib
        - Never store plain text passwords
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode in token (typically user_id, roles)
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
        
    Security Notes:
        - Short expiration time (default 30 minutes)
        - Includes 'exp' claim for automatic expiration
        - Never include sensitive data in payload (it's base64, not encrypted)
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Payload data to encode (typically just user_id)
        
    Returns:
        str: Encoded JWT refresh token
        
    Security Notes:
        - Longer expiration (default 7 days)
        - Should be stored securely (httpOnly cookie or secure storage)
        - Used only to generate new access tokens
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed
        
    Security Notes:
        - Validates signature using secret key
        - Checks expiration automatically
        - Returns 401 for any invalid token
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def sanitize_mongo_query(query_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize user input to prevent NoSQL injection attacks.
    
    Args:
        query_dict: Dictionary potentially containing user input
        
    Returns:
        Dict: Sanitized dictionary with operators removed
        
    Security Notes:
        - Removes MongoDB operators ($gt, $lt, $ne, $where, etc.)
        - Prevents query manipulation attacks
        - Must be called on ALL user input before database queries
        
    Example:
        Input: {"email": {"$ne": None}}  # Malicious attempt to get all users
        Output: {"email": ""}  # Sanitized, won't match
    """
    sanitized = {}
    
    for key, value in query_dict.items():
        # Remove keys starting with $ (MongoDB operators)
        if isinstance(key, str) and key.startswith("$"):
            continue
            
        # Recursively sanitize nested dictionaries
        if isinstance(value, dict):
            sanitized[key] = sanitize_mongo_query(value)
        # Recursively sanitize lists
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_mongo_query(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
            
    return sanitized


def validate_password_strength(password: str) -> bool:
    """
    Validate password meets minimum security requirements.
    
    Args:
        password: Plain text password
        
    Returns:
        bool: True if password meets requirements
        
    Requirements:
        - At least 8 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        
    Note: Enforce this in Pydantic models for automatic validation
    """
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit