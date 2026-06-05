# backend/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.database import get_db
from backend.auth import get_current_user, get_password_hash, create_access_token
import uuid
import os
import shutil
from datetime import datetime

router = APIRouter()

# User registration
@router.post("/auth/register")
async def register(
    full_name: str,
    email: str,
    password: str,
    phone_number: str = None,
    location: str = None,
    skills: str = None,
    education: str = None,
    experience_years: int = 0,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if user exists
    from backend.models import User
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        user_id=uuid.uuid4(),
        full_name=full_name,
        email=email,
        password_hash=get_password_hash(password),
        phone_number=phone_number,
        location=location,
        skills=skills.split(",") if skills else [],
        education=education,
        experience_years=experience_years,
        role="user",
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    
    return {"message": "User registered successfully", "user_id": str(user.user_id)}

# User login
@router.post("/auth/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    from backend.models import User
    from backend.auth import verify_password, create_access_token
    
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({
        "sub": str(user.user_id),
        "email": user.email,
        "role": user.role
    })
    
    return {
        "token": token,
        "user": {
            "user_id": str(user.user_id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "profile_image": user.profile_image
        }
    }

# Get user profile
@router.get("/users/profile")
async def get_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's profile"""
    from backend.models import User, UserActivity, ScamReport
    
    user = db.execute(select(User).where(User.user_id == current_user["user_id"])).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user stats
    jobs_checked = db.execute(select(func.count(UserActivity.activity_id)).where(
        UserActivity.user_id == current_user["user_id"],
        UserActivity.activity_type == "job_checked"
    )).scalar_one_or_none() or 0
    
    reports_submitted = db.execute(select(func.count(ScamReport.report_id)).where(
        ScamReport.reported_by == current_user["user_id"]
    )).scalar_one_or_none() or 0
    
    return {
        "user_id": str(user.user_id),
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "location": user.location,
        "skills": user.skills,
        "education": user.education,
        "experience_years": user.experience_years,
        "bio": user.bio,
        "profile_image": user.profile_image,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "stats": {
            "jobs_checked": jobs_checked,
            "reports_submitted": reports_submitted
        }
    }

# Update user profile
@router.put("/users/profile")
async def update_profile(
    full_name: str = None,
    phone_number: str = None,
    location: str = None,
    skills: str = None,
    education: str = None,
    experience_years: int = None,
    bio: str = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    from backend.models import User
    
    user = db.execute(select(User).where(User.user_id == current_user["user_id"])).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if full_name:
        user.full_name = full_name
    if phone_number:
        user.phone_number = phone_number
    if location:
        user.location = location
    if skills:
        user.skills = skills.split(",")
    if education:
        user.education = education
    if experience_years is not None:
        user.experience_years = experience_years
    if bio:
        user.bio = bio
    
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Profile updated successfully"}

# Upload profile image
@router.post("/users/upload-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile image"""
    from backend.models import User
    
    # Create uploads directory if not exists
    os.makedirs("uploads", exist_ok=True)
    
    # Save file
    file_extension = file.filename.split(".")[-1]
    filename = f"{current_user['user_id']}.{file_extension}"
    file_path = f"uploads/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user profile image URL
    user = db.execute(select(User).where(User.user_id == current_user["user_id"])).scalar_one_or_none()
    if user:
        user.profile_image = f"/uploads/{filename}"
        db.commit()
    
    return {"image_url": f"/uploads/{filename}"}

# Get user activities
@router.get("/users/activities")
async def get_activities(
    limit: int = 20,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's recent activities"""
    from backend.models import UserActivity
    
    activities = db.execute(
        select(UserActivity)
        .where(UserActivity.user_id == current_user["user_id"])
        .order_by(UserActivity.created_at.desc())
        .limit(limit)
    ).scalars().all()
    
    return [
        {
            "activity_id": str(a.activity_id),
            "activity_type": a.activity_type,
            "description": a.details.get("description", "") if a.details else "",
            "icon": a.details.get("icon", "📌") if a.details else "📌",
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in activities
    ]