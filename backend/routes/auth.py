#backend/routes/auth.py

from backend.supabase_client import supabase
from backend.schemas.auth import LoginRequest, RegisterRequest
from backend.auth import hash_password, verify_password, create_access_token, get_current_user
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup")
async def signup(data: RegisterRequest):
    try:
        existing = (
            supabase.table("admin_users")
            .select("id")
            .eq("email", data.email)
            .execute()
        )

        if existing.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = hash_password(data.password)

        response = (
            supabase.table("admin_users")
            .insert({
                "name": data.name,
                "email": data.email,
                "password_hash": hashed_password,
                "role": "user",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create account")

        user = response.data[0]
        token = create_access_token({
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"]
        })

        return {
            "message": "Account created successfully",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Signup failed: {exc}")


# Alias: register → signup (frontend calls /api/auth/register)
@router.post("/register")
async def register(data: RegisterRequest):
    return await signup(data)


@router.post("/login")
async def login(data: LoginRequest):
    response = (
        supabase.table("admin_users").select("*")
        .eq("email", data.email).execute()
    )

    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = response.data[0]

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

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


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    response = (
        supabase.table("admin_users")
        .select("id, name, email, role, created_at")
        .eq("id", str(user_id))
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    user = response.data[0]
    return {
        "id": user["id"],
        "name": user.get("name"),
        "email": user["email"],
        "role": user["role"],
        "created_at": user.get("created_at")
    }


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.put("/profile")
async def update_profile(data: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    updates = {}
    if data.name:
        updates["name"] = data.name
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    response = (
        supabase.table("admin_users")
        .update(updates)
        .eq("id", str(user_id))
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Profile updated", "user": response.data[0]}


@router.post("/change-password")
async def change_password(data: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    resp = supabase.table("admin_users").select("password_hash").eq("id", str(user_id)).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(data.current_password, resp.data[0]["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    new_hash = hash_password(data.new_password)
    supabase.table("admin_users").update({"password_hash": new_hash}).eq("id", str(user_id)).execute()
    return {"message": "Password changed successfully"}


# ── User Settings routes (used by settings.html) ──
@router.get("/delete-account")
async def delete_account_placeholder():
    raise HTTPException(status_code=405, detail="Use POST /auth/delete-account")

@router.post("/delete-account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    try:
        supabase.table("admin_users").delete().eq("id", str(user_id)).execute()
        return {"message": "Account deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

