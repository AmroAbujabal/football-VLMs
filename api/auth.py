"""
api/auth.py

JWT token creation, verification, and the FastAPI dependency
that protects endpoints with Bearer token auth.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Sentinel used to keep bcrypt verification time constant even on cache-miss.
# Must be a real bcrypt hash — bcrypt.verify() will still take ~100ms against it.
_DUMMY_HASH = _pwd_context.hash("__sentinel__")

_JWT_SUB = "sub"

_INVALID_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(academy_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {_JWT_SUB: str(academy_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def _decode_token(token: str) -> UUID:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str | None = payload.get(_JWT_SUB)
        if sub is None:
            raise _INVALID_TOKEN
        return UUID(sub)
    except (JWTError, ValueError):
        raise _INVALID_TOKEN


def get_current_academy_id(token: str = Depends(_oauth2_scheme)) -> UUID:
    """Validate Bearer token and return the academy_id encoded in it."""
    return _decode_token(token)


def constant_time_verify(plain: str, hashed: str | None) -> bool:
    """Run bcrypt verify against `hashed`, falling back to a dummy hash when
    hashed is None. Keeps response time constant regardless of whether the
    academy exists, mitigating timing-based username enumeration."""
    return _pwd_context.verify(plain, hashed if hashed is not None else _DUMMY_HASH)
