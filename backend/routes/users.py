from backend.supabase_client import supabase
from backend.schemas.auth import LoginRequest
from backend.auth import verify_password, create_access_token
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/users", tags=["Users"])
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

    admin = response.data[0]

    if not verify_password(
        data.password, admin["password_hash"]
    ):
        raise HTTPException(
            status_code=401, detail="Invalid credentials"
        )

    token = create_access_token({
        "admin_id": admin["id"],
        "email": admin["email"],
        "role": admin["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": {
            "id": admin["id"],
            "name": admin["name"],
            "email": admin["email"],
            "role": admin["role"]
        }
    }