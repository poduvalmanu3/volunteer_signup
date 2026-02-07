from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    total: int
    users: list[UserListItem]


class UpdateRoleRequest(BaseModel):
    role: str


class UpdateRoleResponse(BaseModel):
    message: str
    user: UserResponse


class DeleteUserResponse(BaseModel):
    message: str
