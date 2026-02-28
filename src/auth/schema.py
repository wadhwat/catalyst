from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class ProfileResponse(BaseModel):
    id: int
    email: EmailStr
    display_name: Optional[str] = None
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
