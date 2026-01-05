from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings


class GeoLocation(BaseModel):
    """
    GeoJSON Point for geospatial queries.
    Format: [longitude, latitude]
    """
    type: str = Field(default="Point", description="GeoJSON type")
    coordinates: List[float] = Field(
        ...,
        description="[longitude, latitude]",
        min_length=2,
        max_length=2
    )
    
    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[float]) -> List[float]:
        """Validate longitude and latitude ranges."""
        lon, lat = v
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v


class Location(BaseModel):
    """
    Location information for cleanup drive.
    Includes address, district, and geospatial data.
    """
    geo: GeoLocation = Field(..., description="Geospatial coordinates")
    address: str = Field(..., min_length=5, max_length=500, description="Full address")
    district: str = Field(..., description="Kerala district")
    state: str = Field(default="Kerala", description="State name")
    
    @field_validator("district")
    @classmethod
    def validate_district(cls, v: str) -> str:
        """Validate district is in Kerala."""
        if v not in settings.KERALA_DISTRICTS:
            raise ValueError(f"District must be one of {settings.KERALA_DISTRICTS}")
        return v


class DriveBase(BaseModel):
    """Base drive model with common fields."""
    title: str = Field(..., min_length=5, max_length=200, description="Drive title")
    description: str = Field(..., min_length=20, max_length=2000, description="Drive description")
    type: str = Field(..., description="Type of cleanup drive")
    date_time: datetime = Field(..., description="Drive date and time")
    location: Location = Field(..., description="Drive location")
    max_volunteers: int = Field(..., ge=1, le=1000, description="Maximum volunteers")
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate drive type."""
        if v not in settings.DRIVE_TYPES:
            raise ValueError(f"type must be one of {settings.DRIVE_TYPES}")
        return v
    
    @field_validator("date_time")
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        """Ensure drive is scheduled in the future."""
        if v <= datetime.utcnow():
            raise ValueError("Drive date must be in the future")
        return v


class DriveCreate(DriveBase):
    """
    Drive creation model.
    Organizer ID added from authenticated user.
    """
    pass


class DriveUpdate(BaseModel):
    """
    Drive update model.
    All fields optional for partial updates.
    """
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=2000)
    type: Optional[str] = None
    date_time: Optional[datetime] = None
    location: Optional[Location] = None
    max_volunteers: Optional[int] = Field(None, ge=1, le=1000)
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate drive type if provided."""
        if v is not None and v not in settings.DRIVE_TYPES:
            raise ValueError(f"type must be one of {settings.DRIVE_TYPES}")
        return v
    
    @field_validator("date_time")
    @classmethod
    def validate_future_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure drive is scheduled in the future if provided."""
        if v is not None and v <= datetime.utcnow():
            raise ValueError("Drive date must be in the future")
        return v


class DriveInDB(DriveBase):
    """
    Drive model as stored in database.
    """
    id: str = Field(..., alias="_id")
    organizer_id: str = Field(..., description="ID of organizer who created drive")
    status: str = Field(
        default="draft",
        description="Drive status: draft, published, ongoing, completed, cancelled"
    )
    current_volunteers: int = Field(default=0, description="Current number of registered volunteers")
    registration_open: bool = Field(default=True, description="Whether registration is open")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}


class DriveResponse(DriveBase):
    """
    Drive response model for API responses.
    """
    id: str = Field(..., alias="_id")
    organizer_id: str
    status: str
    current_volunteers: int
    registration_open: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"populate_by_name": True}


class DriveListResponse(BaseModel):
    """
    Paginated list of drives.
    """
    drives: List[DriveResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class DriveSearchFilters(BaseModel):
    """
    Search filters for drive queries.
    """
    district: Optional[str] = None
    type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[str] = Field(default="published")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @field_validator("district")
    @classmethod
    def validate_district(cls, v: Optional[str]) -> Optional[str]:
        """Validate district if provided."""
        if v is not None and v not in settings.KERALA_DISTRICTS:
            raise ValueError(f"District must be one of {settings.KERALA_DISTRICTS}")
        return v
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate drive type if provided."""
        if v is not None and v not in settings.DRIVE_TYPES:
            raise ValueError(f"type must be one of {settings.DRIVE_TYPES}")
        return v
    
    @model_validator(mode='after')
    def validate_date_range(self):
        """Ensure date_from is before date_to."""
        if self.date_from and self.date_to:
            if self.date_from >= self.date_to:
                raise ValueError("date_from must be before date_to")
        return self