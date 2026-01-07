"""
Application configuration management using Pydantic Settings.
Environment-based configuration with validation and type safety.
"""

from typing import List, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    All sensitive data comes from environment variables.
    """
    
    # MongoDB Configuration
    MONGODB_URL: str = Field(
        default="mongodb://127.0.0.1:27017",
        description="MongoDB connection string"
    )
    DATABASE_NAME: str = Field(
        default="cleanup_platform",
        description="MongoDB database name"
    )
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(
        ...,  # Required field
        description="Secret key for JWT token generation (MUST be strong in production)"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm for JWT encoding/decoding"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    # Application Configuration
    ENVIRONMENT: Literal["development", "production"] = Field(
        default="development",
        description="Application environment"
    )
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API version 1 prefix"
    )
    PROJECT_NAME: str = Field(
        default="Kerala Cleanup Platform",
        description="Project name for API documentation"
    )
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Number of requests allowed per minute per IP"
    )
    
    # Kerala Districts for validation
    KERALA_DISTRICTS: List[str] = [
        "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha",
        "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad",
        "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod"
    ]
    
    # Drive Types
    DRIVE_TYPES: List[str] = [
        "beach_cleanup", "river_cleanup", "park_cleanup", 
        "street_cleanup", "road_cleanup", "other"
    ]
    
    # Age Bands
    AGE_BANDS: List[str] = ["under13", "13-17", "18+"]
    
    # User Roles
    USER_ROLES: List[str] = ["volunteer", "organizer", "admin"]
    
    # Registration deadline (hours before drive start)
    REGISTRATION_DEADLINE_HOURS: int = Field(
        default=1,
        description="Hours before drive start when registration closes"
    )
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Default number of items per page"
    )
    MAX_PAGE_SIZE: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of items per page"
    )
    
    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in v.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables
    )


# Global settings instance
settings = Settings()