from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class RegistrationCreate(BaseModel):
    """
    Registration creation model.
    User ID comes from authenticated user.
    """
    drive_id: str = Field(..., description="ID of drive to register for")


class RegistrationInDB(BaseModel):
    """
    Registration as stored in database.
    """
    id: str = Field(..., alias="_id")
    drive_id: str = Field(..., description="Drive ID")
    user_id: str = Field(..., description="User ID")
    status: str = Field(
        default="confirmed",
        description="Registration status: confirmed, cancelled, waitlist"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}


class RegistrationResponse(BaseModel):
    """
    Registration response model.
    """
    id: str = Field(..., alias="_id")
    drive_id: str
    user_id: str
    status: str
    created_at: datetime
    
    model_config = {"populate_by_name": True}


class MyRegistrationsResponse(BaseModel):
    """
    User's registrations with drive details.
    """
    registrations: List[dict]  # Contains registration + drive info
    total: int


class AttendanceCreate(BaseModel):
    """
    Mark attendance for a volunteer.
    """
    user_id: str = Field(..., description="User ID to mark attendance for")
    attended: bool = Field(..., description="Whether user attended")
    hours_logged: Optional[float] = Field(None, ge=0, le=24, description="Hours volunteered")


class AttendanceInDB(BaseModel):
    """
    Attendance record as stored in database.
    """
    id: str = Field(..., alias="_id")
    drive_id: str = Field(..., description="Drive ID")
    user_id: str = Field(..., description="User ID")
    attended: bool = Field(..., description="Attendance status")
    hours_logged: Optional[float] = Field(None, description="Hours volunteered")
    marked_by: str = Field(..., description="Organizer who marked attendance")
    marked_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}


class AttendanceResponse(BaseModel):
    """
    Attendance response model.
    """
    id: str = Field(..., alias="_id")
    drive_id: str
    user_id: str
    attended: bool
    hours_logged: Optional[float]
    marked_by: str
    marked_at: datetime
    
    model_config = {"populate_by_name": True}


class ParticipantResponse(BaseModel):
    """
    Participant info for organizer view.
    Privacy-first: minimal data exposure.
    """
    registration_id: str = Field(..., description="Registration ID")
    first_name: str = Field(..., description="First name only")
    age_band: str = Field(..., description="Age category")
    registration_status: str = Field(..., description="Registration status")
    attendance_status: Optional[str] = Field(None, description="Attendance if marked")
    hours_logged: Optional[float] = Field(None, description="Hours if attendance marked")


class ParticipantsListResponse(BaseModel):
    """
    Paginated list of participants.
    """
    participants: List[ParticipantResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class MessageCreate(BaseModel):
    """
    In-app message creation.
    Proxy for organizer-volunteer communication without exposing contact info.
    """
    recipient_id: str = Field(..., description="Recipient user ID")
    drive_id: str = Field(..., description="Related drive ID")
    subject: str = Field(..., min_length=3, max_length=200, description="Message subject")
    body: str = Field(..., min_length=10, max_length=2000, description="Message body")


class MessageInDB(BaseModel):
    """
    Message as stored in database.
    """
    id: str = Field(..., alias="_id")
    sender_id: str = Field(..., description="Sender user ID")
    recipient_id: str = Field(..., description="Recipient user ID")
    drive_id: str = Field(..., description="Related drive ID")
    subject: str
    body: str
    read: bool = Field(default=False, description="Message read status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}


class MessageResponse(BaseModel):
    """
    Message response model.
    """
    id: str = Field(..., alias="_id")
    sender_id: str
    recipient_id: str
    drive_id: str
    subject: str
    body: str
    read: bool
    created_at: datetime
    
    model_config = {"populate_by_name": True}