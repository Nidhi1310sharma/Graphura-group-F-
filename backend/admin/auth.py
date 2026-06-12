# admin.auth.py
from fastapi import Depends, HTTPException
from backend.auth import get_current_user

async def admin_required(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
