"""
Pydantic models for user-related data validation and serialization.
Enforces privacy-first design with age bands instead of DOB.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
import phonenumbers # remove the usage of this dependency, use regex to validate indian phone numbers

from app.core.config import settings


class ConsentFlags(BaseModel):
    """
    User consent tracking for privacy compliance.
    """
    terms_accepted: bool = Field(..., description="User accepted terms of service")
    privacy_accepted: bool = Field(..., description="User accepted privacy policy")
    guardian_consent: Optional[bool] = Field(
        None,
        description="Guardian consent for minors (required for under 18)"
    )


class UserBase(BaseModel):
    """Base user model with common fields."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number in Indian format")
    age_band: str = Field(..., description="Age category: under13, 13-17, 18+")
    
    @field_validator("age_band")
    @classmethod
    def validate_age_band(cls, v: str) -> str:
        """Validate age band is one of the allowed values."""
        if v not in settings.AGE_BANDS:
            raise ValueError(f"age_band must be one of {settings.AGE_BANDS}")
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        Validate Indian phone number format.
        Accepts: +91XXXXXXXXXX or 10-digit number
        """
        try:
            # Remove spaces and dashes
            clean_phone = v.replace(" ", "").replace("-", "")
            
            # Add +91 if not present
            if not clean_phone.startswith("+"):
                clean_phone = f"+91{clean_phone}"
            
            # Parse and validate
            parsed = phonenumbers.parse(clean_phone, "IN")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid Indian phone number")
            
            # Return in standard format
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
        except Exception:
            raise ValueError("Invalid phone number format. Use +91XXXXXXXXXX or 10 digits")


class UserCreate(UserBase):
    """
    User registration model.
    Requires password and consent flags.
    """
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    consent_flags: ConsentFlags
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Enforce password strength requirements.
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        return v
    
    @model_validator(mode='after')
    def validate_minor_consent(self):
        """
        Ensure guardian consent is provided for minors.
        Security Note: COPPA compliance - minors need parental consent.
        """
        if self.age_band in ["under13", "13-17"]:
            if not self.consent_flags.guardian_consent:
                raise ValueError("Guardian consent required for users under 18")
        return self


class UserUpdate(BaseModel):
    """
    User profile update model.
    All fields optional for partial updates.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone if provided."""
        if v is None:
            return v
        return UserBase.validate_phone(v)


class UserInDB(UserBase):
    """
    User model as stored in database.
    Includes internal fields not exposed to users.
    """
    id: str = Field(..., alias="_id", description="User ID")
    hashed_password: str = Field(..., description="Bcrypt hashed password")
    roles: List[str] = Field(default=["volunteer"], description="User roles")
    consent_flags: ConsentFlags
    is_active: bool = Field(default=True, description="Account active status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}


class UserResponse(UserBase):
    """
    User response model for API responses.
    Excludes sensitive data like password.
    """
    id: str = Field(..., alias="_id")
    roles: List[str]
    is_active: bool
    created_at: datetime
    
    model_config = {"populate_by_name": True}


class UserMinimalResponse(BaseModel):
    """
    Minimal user data for organizer views.
    Privacy-first: only first name and age band exposed.
    """
    first_name: str = Field(..., description="First name only")
    age_band: str = Field(..., description="Age category")
    
    @classmethod
    def from_user(cls, user: UserInDB) -> "UserMinimalResponse":
        """Create minimal response from full user object."""
        first_name = user.name.split()[0] if user.name else "Anonymous"
        return cls(first_name=first_name, age_band=user.age_band)


class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation with new password."""
    token: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password strength for reset."""
        return UserCreate.validate_password_strength(v)