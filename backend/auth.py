#backend/auth.py

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto"
)

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

    return jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM
    )