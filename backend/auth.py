#backend/auth.py

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional

load_dotenv()

pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto"
)

SUPABASE_ANON_KEY=os.getenv("SUPABASE_ANON_KEY")
SECRET_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ALGORITHM = os.getenv("ALGORITHM")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
)

security = HTTPBearer()


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(
    plain_password: str, hashed_password: str
):
    return pwd_context.verify(
        plain_password,hashed_password
    )


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})
    # use a dedicated JWT secret for access tokens if provided
    key = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
    return jwt.encode(
        to_encode, key, algorithm=ALGORITHM
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY or SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
):
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY or SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if not payload or "user_id" not in payload:
        return None

    return payload