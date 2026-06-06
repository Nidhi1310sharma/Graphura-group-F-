# import os
# import shutil
# import uuid
# from datetime import datetime, timezone
# from pathlib import Path
# from typing import List, Optional


# from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
# from pydantic import EmailStr
# from sqlalchemy import func, select
# from sqlalchemy.orm import Session

# from backend.auth import create_access_token, get_current_user, get_password_hash, verify_password
# from backend.database import get_db
# from backend.models import ScamReport, User, UserActivity
# from backend.schemas.users import (
#     LoginRequest,
#     ProfileResponse,
#     RegisterRequest,
#     UpdateProfileRequest,
# )

# router = APIRouter(prefix="/users", tags=["Users"])
# AUTH_ROUTER = APIRouter(prefix="/auth", tags=["Authentication"])

# UPLOAD_DIR = Path("uploads")


# # --- Authentication Endpoints ---


# @AUTH_ROUTER.post("/register", status_code=status.HTTP_201_CREATED)
# async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
#     """Register a new user securely using a JSON request body."""
#     existing = db.execute(
#         select(User).where(User.email == payload.email)
#     ).scalar_one_or_none()

#     if existing:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered",
#         )

#     user = User(
#         user_id=uuid.uuid4(),
#         full_name=payload.full_name,
#         email=payload.email,
#         password_hash=get_password_hash(payload.password),
#         phone_number=payload.phone_number,
#         location=payload.location,
#         skills=payload.skills.split(",") if payload.skills else [],
#         education=payload.education,
#         experience_years=payload.experience_years,
#         role="user",
#         created_at=datetime.now(timezone.utc),
#     )

#     db.add(user)
#     db.commit()

#     return {"message": "User registered successfully", "user_id": str(user.user_id)}


# @AUTH_ROUTER.post("/login")
# async def login(payload: LoginRequest, db: Session = Depends(get_db)):
#     """Login user and return a JWT access token."""
#     user = db.execute(
#         select(User).where(User.email == payload.email)
#     ).scalar_one_or_none()

#     if not user or not verify_password(payload.password, user.password_hash):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid credentials",
#         )

#     token = create_access_token(
#         {"sub": str(user.user_id), "email": user.email, "role": user.role}
#     )

#     return {
#         "token": token,
#         "user": {
#             "user_id": str(user.user_id),
#             "full_name": user.full_name,
#             "email": user.email,
#             "role": user.role,
#             "profile_image": user.profile_image,
#         },
#     }


# # --- User Profile Endpoints ---


# @router.get("/profile", response_model=ProfileResponse)
# async def get_profile(
#     current_user=Depends(get_current_user), db: Session = Depends(get_db)
# ):
#     """Get current user's profile and aggregated metrics."""
#     user = db.execute(
#         select(User).where(User.user_id == current_user["user_id"])
#     ).scalar_one_or_none()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     # Aggregate performance stats
#     jobs_checked = (
#         db.execute(
#             select(func.count(UserActivity.activity_id)).where(
#                 UserActivity.user_id == current_user["user_id"],
#                 UserActivity.activity_type == "job_checked",
#             )
#         ).scalar_one_or_none()
#         or 0
#     )

#     reports_submitted = (
#         db.execute(
#             select(func.count(ScamReport.report_id)).where(
#                 ScamReport.reported_by == current_user["user_id"]
#             )
#         ).scalar_one_or_none()
#         or 0
#     )

#     return {
#         "user_id": str(user.user_id),
#         "full_name": user.full_name,
#         "email": user.email,
#         "phone_number": user.phone_number,
#         "location": user.location,
#         "skills": user.skills,
#         "education": user.education,
#         "experience_years": user.experience_years,
#         "bio": user.bio,
#         "profile_image": user.profile_image,
#         "role": user.role,
#         "created_at": user.created_at.isoformat() if user.created_at else None,
#         "stats": {
#             "jobs_checked": jobs_checked,
#             "reports_submitted": reports_submitted,
#         },
#     }


# @router.put("/profile")
# async def update_profile(
#     payload: UpdateProfileRequest,
#     current_user=Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     """Update active user profile fields dynamically."""
#     user = db.execute(
#         select(User).where(User.user_id == current_user["user_id"])
#     ).scalar_one_or_none()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     # Track updates systematically
#     update_data = payload.model_dump(exclude_unset=True)

#     for field, value in update_data.items():
#         if field == "skills" and value is not None:
#             user.skills = value.split(",")
#         else:
#             setattr(user, field, value)

#     user.updated_at = datetime.now(timezone.utc)
#     db.commit()

#     return {"message": "Profile updated successfully"}


# @router.post("/upload-image")
# async def upload_profile_image(
#     file: UploadFile = File(...),
#     current_user=Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     """Upload and bind an avatar image to the current user."""
#     UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

#     file_extension = Path(file.filename).suffix
#     filename = f"{current_user['user_id']}{file_extension}"
#     file_path = UPLOAD_DIR / filename

#     with file_path.open("wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     user = db.execute(
#         select(User).where(User.user_id == current_user["user_id"])
#     ).scalar_one_or_none()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     user.profile_image = f"/uploads/{filename}"
#     db.commit()

#     return {"image_url": user.profile_image}


# @router.get("/activities")
# async def get_activities(
#     limit: int = 20,
#     current_user=Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     """Get chronological user action history logs."""
#     activities = (
#         db.execute(
#             select(UserActivity)
#             .where(UserActivity.user_id == current_user["user_id"])
#             .order_by(UserActivity.created_at.desc())
#             .limit(limit)
#         )
#         .scalars()
#         .all()
#     )

#     return [
#         {
#             "activity_id": str(a.activity_id),
#             "activity_type": a.activity_type,
#             "description": (a.details or {}).get("description", ""),
#             "icon": (a.details or {}).get("icon", "📌"),
#             "created_at": a.created_at.isoformat() if a.created_at else None,
#         }
#         for a in activities
#     ]


# # Include authentication endpoints under root
# router.include_router(AUTH_ROUTER)
