#backend/schemas/community.py
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class CreatePostRequest(BaseModel):
    user_id: UUID
    post_title: str
    content: str
    post_type: str  # e.g., "discussion", "question", "report"
    # report_id: Optional[int] = None  # For posts that are reports of scams
    
class UpdatePostRequest(BaseModel):
    post_title: Optional[str] = None
    content: Optional[str] = None
    post_type: Optional[str] = None

class UpdateCommentRequest(BaseModel):
    content: Optional[str] = None


class CreateCommentRequest(BaseModel):
    user_id: UUID
    content: str
    
class VoteRequest(BaseModel):
    user_id: UUID
    vote_type: int  # +1 for upvote, -1 for downvote