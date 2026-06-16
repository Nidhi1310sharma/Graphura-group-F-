# backend/routes/user.py
from fastapi import APIRouter, Depends
from backend.auth import get_current_user

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/settings")
async def get_settings(current_user: dict = Depends(get_current_user)):
    return {
        "notifications": {"email_alerts": True, "community_updates": True, "weekly_digest": False},
        "privacy": {"profile_visible": True, "reports_visible": False}
    }

@router.post("/settings/notifications")
async def update_notifications(current_user: dict = Depends(get_current_user)):
    return {"message": "Notification settings updated"}

@router.post("/settings/privacy")
async def update_privacy(current_user: dict = Depends(get_current_user)):
    return {"message": "Privacy settings updated"}
