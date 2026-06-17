#backend/schemas/community.py
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class CreatePostRequest(BaseModel):
    post_title: str
    content: str
    post_type: str  # "discussion", "question", "report", "warning"
    company: Optional[str] = None
    domain: Optional[str] = None
    # user_id comes from JWT token, not request body

class UpdatePostRequest(BaseModel):
    post_title: Optional[str] = None
    content: Optional[str] = None
    post_type: Optional[str] = None

class UpdateCommentRequest(BaseModel):
    content: Optional[str] = None

class CreateCommentRequest(BaseModel):
    content: str
    # user_id comes from JWT token, not request body

class VoteRequest(BaseModel):
    vote_type: int  # +1 for upvote, -1 for downvote
    # user_id comes from JWT token, not request body
