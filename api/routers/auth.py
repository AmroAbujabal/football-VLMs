"""
api/routers/auth.py

Authentication endpoint — exchange academy credentials for a JWT.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.auth import constant_time_verify, create_access_token
from api.deps import get_db
from database.models import Academy

router = APIRouter()

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/token")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Exchange academy_id + password for a JWT Bearer token."""
    try:
        academy_id = UUID(form.username)
    except ValueError:
        raise _INVALID_CREDENTIALS

    academy = db.get(Academy, academy_id)
    # Always run bcrypt — constant_time_verify uses a dummy hash when
    # academy is missing so response time doesn't reveal whether the ID exists.
    password_ok = constant_time_verify(
        form.password,
        academy.password_hash if academy is not None else None,
    )
    if not password_ok or academy is None:
        raise _INVALID_CREDENTIALS

    return {
        "access_token": create_access_token(academy.id),
        "token_type": "bearer",
    }
