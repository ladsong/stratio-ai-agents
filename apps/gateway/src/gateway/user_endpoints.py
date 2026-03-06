"""User management API endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.repositories.user_repo import UserRepository
from gateway.dependencies import get_db, get_request_id, verify_auth
from gateway.schemas import (
    UserContactCreate,
    UserContactResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=UserResponse, dependencies=[Depends(verify_auth)])
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> UserResponse:
    """Create a new user."""
    user_id = str(uuid.uuid4())
    repo = UserRepository(db)
    user = repo.create(
        user_id=user_id,
        name=user_data.name,
        role=user_data.role,
        system_prompt=user_data.system_prompt,
        meta=user_data.meta,
    )
    return UserResponse.model_validate(user)


@router.get("", response_model=list[UserResponse], dependencies=[Depends(verify_auth)])
def list_users(
    limit: int = 100,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[UserResponse]:
    """List all users."""
    repo = UserRepository(db)
    users = repo.list_all(limit=limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(verify_auth)])
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> UserResponse:
    """Get a user by ID."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse, dependencies=[Depends(verify_auth)])
def update_user(
    user_id: str,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> UserResponse:
    """Update a user."""
    repo = UserRepository(db)
    user = repo.update(
        user_id=user_id,
        name=update_data.name,
        role=update_data.role,
        system_prompt=update_data.system_prompt,
        meta=update_data.meta,
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", dependencies=[Depends(verify_auth)])
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> dict[str, str]:
    """Delete a user."""
    repo = UserRepository(db)
    deleted = repo.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted", "id": user_id}


@router.post("/{user_id}/contacts", response_model=UserContactResponse, dependencies=[Depends(verify_auth)])
def add_user_contact(
    user_id: str,
    contact_data: UserContactCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> UserContactResponse:
    """Add a contact to a user."""
    repo = UserRepository(db)
    
    # Verify user exists
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if contact already exists
    existing = repo.get_contact(contact_data.channel, contact_data.contact_id)
    if existing:
        raise HTTPException(status_code=409, detail="Contact already exists for another user")
    
    contact_id = str(uuid.uuid4())
    contact = repo.add_contact(
        contact_id_val=contact_id,
        user_id=user_id,
        channel=contact_data.channel,
        contact_id=contact_data.contact_id,
        meta=contact_data.meta,
    )
    return UserContactResponse.model_validate(contact)


@router.get("/contacts/{channel}/{contact_id}", response_model=UserResponse, dependencies=[Depends(verify_auth)])
def get_user_by_contact(
    channel: str,
    contact_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> UserResponse:
    """Get a user by their contact information."""
    repo = UserRepository(db)
    user = repo.get_by_contact(channel, contact_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found for this contact")
    return UserResponse.model_validate(user)
