from fastapi import APIRouter, HTTPException
from backend.supabase_client import supabase
from backend.schemas.community import CreatePostRequest, CreateCommentRequest, VoteRequest
from datetime import datetime, timezone

router = APIRouter(prefix="/community", tags=["Community"])


#to creaete a post in the community forum, which can be a discussion, question, or report of a scam. 
# The post will be associated with the user who created it and can optionally link to a specific scam report if it's a report post.
@router.post("/posts")
async def create_post(data: CreatePostRequest):
    try:
        response = (
            supabase.table("community_posts")
            .insert({
                "user_id": data.user_id,
                "post_title": data.post_title,
                "content": data.content,
                "post_type": data.post_type,
                "report_id": data.report_id,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
            })
            .execute()
        )

        if not response.data:
            return {"message": "Failed to create post"}

        return {
            "message": "Post created successfully",
            "post": response.data[0]
        }
    except Exception as exc:
        return {"message": f"Error creating post: {exc}"}

# to retrieve all posts in the community forum, with optional filtering by post type (e.g., discussion, question, report) and pagination support.
@router.get("/posts")
async def get_posts():

    response = (
            supabase.table("community_posts")
            .select("*")
            .eq("status", "active")  # Only fetch active posts
            .order("created_at", desc=True)
            .execute()
        )
    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Posts not found"
        )

    return response.data[0]
    
    
# to get a specific post by its ID, including the post details and any associated comments. This allows users to view the content of a post and engage with it through comments.
@router.get("/posts/{post_id}")
async def get_post(post_id: str):

    response = (
        supabase.table("community_posts")
        .select("*")
        .eq("post_id", post_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    return response.data[0]

# create a comment on a specific post, allowing users to engage in discussions and provide feedback on posts in the community forum. 
# The comment will be associated with the user who created it and the post it belongs to.
@router.post("/posts/{post_id}/comments")
async def create_comment(post_id: str, data: CreateCommentRequest):
    response = (
        supabase.table("community_comments")
        .insert({
            "user_id": data.user_id,
            "post_id": post_id,
            "content": data.content,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat()
        })
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=400,
            detail="Failed to create comment"
        )

    return {
        "message": "Comment created successfully",
        "comment": response.data[0]
    }
    
# get comments for a specific post, allowing users to view the discussions and feedback associated with a post in the community forum.
@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: str):
    response=(
        supabase.table("community_comments")
        .select("*")
        .eq("post_id", post_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data[0]

@router.post("/posts/{post_id}/vote")
async def vote_post(post_id: str, data: VoteRequest):
    # Check if the user has already voted on this post
    existing_vote = (
        supabase.table("community_votes")
        .select("*")
        .eq("user_id", data.user_id)
        .eq("post_id", post_id)
        .execute()
    )

    if existing_vote.data:
        # If the user has already voted, update their vote
        response = (
            supabase.table("community_votes")
            .update({"vote_type": data.vote_type})
            .eq("user_id", data.user_id)
            .eq("post_id", post_id)
            .execute()
        )
    else:
        # If the user hasn't voted yet, create a new vote
        response = (
            supabase.table("community_votes")
            .insert({
                "user_id": data.user_id,
                "post_id": post_id,
                "vote_type": data.vote_type,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
            })
            .execute()
        )

    if not response.data:
        raise HTTPException(
            status_code=400,
            detail="Failed to record vote"
        )

    return {"message": "Vote recorded successfully"}