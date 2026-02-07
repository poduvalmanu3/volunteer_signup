from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.deps import get_db
from app.models.user import User
from app.schemas.user import (
    UserListResponse,
    UserListItem,
    UpdateRoleRequest,
    UpdateRoleResponse,
    DeleteUserResponse,
)
from app.core.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse, dependencies=[Depends(require_admin)])
def list_all_users(db: Session = Depends(get_db)):
    """
    Admin-only endpoint: List all users in the system.
    Requires ADMIN role.
    """
    users = db.query(User).all()
    return UserListResponse(
        total=len(users),
        users=[UserListItem.model_validate(user) for user in users],
    )


@router.delete(
    "/users/{user_id}",
    response_model=DeleteUserResponse,
    dependencies=[Depends(require_admin)],
)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Admin-only endpoint: Delete a user by ID.
    Requires ADMIN role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user_name = user.name
    db.delete(user)
    db.commit()

    return DeleteUserResponse(message=f"User {user_name} deleted successfully")


@router.patch(
    "/users/{user_id}/role",
    response_model=UpdateRoleResponse,
    dependencies=[Depends(require_admin)],
)
def update_user_role(
    user_id: UUID,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint: Update a user's role.
    Requires ADMIN role.
    """
    if payload.role not in ["USER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be USER or ADMIN",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    old_role = user.role
    user.role = payload.role
    db.commit()
    db.refresh(user)

    return UpdateRoleResponse(
        message=f"User role updated from {old_role} to {payload.role}",
        user=user,
    )
