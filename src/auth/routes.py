from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.auth import db
from src.auth.schema import (
    LoginRequest,
    ProfileResponse,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
)
from src.auth.security import create_access_token, decode_access_token, hash_password, verify_password

router = APIRouter(prefix='/auth', tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login', auto_error=False)


def _row_to_profile(row) -> ProfileResponse:
    return ProfileResponse(
        id=row['id'],
        email=row['email'],
        display_name=row['display_name'],
        created_at=datetime.fromisoformat(row['created_at']),
    )


def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[ProfileResponse]:
    if not token:
        return None
    payload = decode_access_token(token)
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token payload')
    row = db.get_user_by_id(int(user_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return _row_to_profile(row)


def require_user(user: Optional[ProfileResponse] = Depends(get_current_user)) -> ProfileResponse:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    return user


@router.post('/register', response_model=TokenResponse)
def register(payload: RegisterRequest) -> TokenResponse:
    if db.get_user_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already registered')
    password_hash = hash_password(payload.password)
    created_at = datetime.now(timezone.utc).isoformat()
    user_id = db.create_user(payload.email, password_hash, payload.display_name, created_at)
    token = create_access_token({'sub': str(user_id), 'email': payload.email})
    return TokenResponse(access_token=token)


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    row = db.get_user_by_email(payload.email)
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    if not verify_password(payload.password, row['password_hash']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    token = create_access_token({'sub': str(row['id']), 'email': row['email']})
    return TokenResponse(access_token=token)


@router.get('/me', response_model=ProfileResponse)
def me(user: ProfileResponse = Depends(require_user)) -> ProfileResponse:
    return user


@router.put('/me', response_model=ProfileResponse)
def update_me(
    payload: UpdateProfileRequest,
    user: ProfileResponse = Depends(require_user),
) -> ProfileResponse:
    db.update_display_name(user.id, payload.display_name)
    row = db.get_user_by_id(user.id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return _row_to_profile(row)
