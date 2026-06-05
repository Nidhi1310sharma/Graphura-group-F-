# backend/routes/community.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.database import get_db
from backend.auth import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

# Create a community post
@router.post("/community/posts")
async def create_post(
    content: str,
    scam_report_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new community post"""
    from backend.models import CommunityPost, User, UserActivity
    
    user = db.execute(select(User).where(User.user_id == current_user["user_id"])).scalar_one_or_none()
    
    post = CommunityPost(
        post_id=uuid.uuid4(),
        user_id=current_user["user_id"],
        user_name=user.full_name if user else "Anonymous",
        user_image=user.profile_image if user else None,
        content=content,
        scam_report_id=scam_report_id,
        likes=0,
        comments_count=0,
        shares=0,
        created_at=datetime.utcnow()
    )
    db.add(post)
    
    # Log activity
    activity = UserActivity(
        activity_id=uuid.uuid4(),
        user_id=current_user["user_id"],
        activity_type="post_created",
        details={
            "description": f"Posted to community",
            "icon": "💬"
        },
        created_at=datetime.utcnow()
    )
    db.add(activity)
    db.commit()
    
    return {
        "post_id": str(post.post_id),
        "message": "Post created successfully"
    }

# Get community posts
@router.get("/community/posts")
async def get_posts(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all community posts"""
    from backend.models import CommunityPost, ScamReport
    
    posts = db.execute(
        select(CommunityPost, ScamReport.company_name, ScamReport.scam_type)
        .outerjoin(ScamReport, CommunityPost.scam_report_id == ScamReport.report_id)
        .order_by(CommunityPost.created_at.desc())
        .limit(limit)
    ).all()
    
    return [
        {
            "post_id": str(p.CommunityPost.post_id),
            "user_id": str(p.CommunityPost.user_id) if p.CommunityPost.user_id else None,
            "user_name": p.CommunityPost.user_name or "Anonymous",
            "user_image": p.CommunityPost.user_image,
            "content": p.CommunityPost.content,
            "likes": p.CommunityPost.likes,
            "comments_count": p.CommunityPost.comments_count,
            "shares": p.CommunityPost.shares,
            "scam_company": p.company_name,
            "scam_type": p.scam_type,
            "created_at": p.CommunityPost.created_at.isoformat() if p.CommunityPost.created_at else None
        }
        for p in posts
    ]

# Like a post
@router.post("/community/posts/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Like a community post"""
    from backend.models import CommunityPost, CommunityLike
    
    # Check if already liked
    existing_like = db.execute(
        select(CommunityLike)
        .where(
            CommunityLike.post_id == post_id,
            CommunityLike.user_id == current_user["user_id"]
        )
    ).scalar_one_or_none()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        db.execute(select(CommunityPost).where(CommunityPost.post_id == post_id)).scalar_one().likes -= 1
    else:
        # Like
        like = CommunityLike(
            like_id=uuid.uuid4(),
            post_id=post_id,
            user_id=current_user["user_id"],
            created_at=datetime.utcnow()
        )
        db.add(like)
        db.execute(select(CommunityPost).where(CommunityPost.post_id == post_id)).scalar_one().likes += 1
    
    db.commit()
    
    return {"message": "Like toggled"}

# Add comment to post
@router.post("/community/posts/{post_id}/comments")
async def add_comment(
    post_id: str,
    content: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a post"""
    from backend.models import CommunityComment, CommunityPost, User
    
    user = db.execute(select(User).where(User.user_id == current_user["user_id"])).scalar_one_or_none()
    
    comment = CommunityComment(
        comment_id=uuid.uuid4(),
        post_id=post_id,
        user_id=current_user["user_id"],
        user_name=user.full_name if user else "Anonymous",
        user_image=user.profile_image if user else None,
        content=content,
        likes=0,
        created_at=datetime.utcnow()
    )
    db.add(comment)
    
    # Update comment count on post
    post = db.execute(select(CommunityPost).where(CommunityPost.post_id == post_id)).scalar_one_or_none()
    if post:
        post.comments_count += 1
    
    db.commit()
    
    return {
        "comment_id": str(comment.comment_id),
        "message": "Comment added"
    }

# Get comments for a post
@router.get("/community/posts/{post_id}/comments")
async def get_comments(
    post_id: str,
    db: Session = Depends(get_db)
):
    """Get all comments for a post"""
    from backend.models import CommunityComment
    
    comments = db.execute(
        select(CommunityComment)
        .where(CommunityComment.post_id == post_id)
        .order_by(CommunityComment.created_at.asc())
    ).scalars().all()
    
    return [
        {
            "comment_id": str(c.comment_id),
            "user_id": str(c.user_id) if c.user_id else None,
            "user_name": c.user_name or "Anonymous",
            "user_image": c.user_image,
            "content": c.content,
            "likes": c.likes,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in comments
    ]