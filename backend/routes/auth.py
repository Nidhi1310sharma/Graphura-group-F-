#backend/routes/auth.py

from backend.supabase_client import supabase
from backend.schemas.auth import LoginRequest, RegisterRequest
from backend.auth import hash_password, verify_password, create_access_token
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
async def signup(data: RegisterRequest):
    try:
        # Check if email already exists
        existing = (
            supabase.table("admin_users")
            .select("id")
            .eq("email", data.email)
            .execute()
        )

        if existing.data:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        hashed_password = hash_password(data.password)

        response = (
            supabase.table("admin_users")
            .insert({
                "name": data.name,
                "email": data.email,
                "password_hash": hashed_password,
                "role": "user",
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
            })
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create account"
            )

        return {
            "message": "Account created successfully",
            "user_id": response.data[0]["id"]
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Signup failed: {exc}"
        )

@router.post("/login")
async def login(data: LoginRequest):

    response = (
        supabase.table("admin_users").select("*")
        .eq("email", data.email).execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=401, detail="Invalid credentials"
        )

    user = response.data[0]

    if not verify_password(
        data.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=401, detail="Invalid credentials"
        )

    token = create_access_token({
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }