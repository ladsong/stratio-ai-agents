from __future__ import annotations

import os
import uuid
from typing import Generator

from fastapi import Header, HTTPException, Request
from sqlalchemy.orm import Session

from core.db.engine import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_auth(authorization: str | None = Header(None)) -> None:
    bearer_token = os.environ.get("AUTH_BEARER_TOKEN", "")
    
    if not bearer_token:
        return
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    if token != bearer_token:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_request_id(request: Request, x_request_id: str | None = Header(None)) -> str:
    if x_request_id:
        return x_request_id
    
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    return request_id
