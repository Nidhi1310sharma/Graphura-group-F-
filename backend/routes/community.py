from fastapi import APIRouter, HTTPException, Depends
from backend.supabase_client import supabase
from backend.schemas.community import CreatePostRequest, CreateCommentRequest, UpdatePostRequest, UpdateCommentRequest, VoteRequest
from datetime import datetime, timezone
from typing import Optional
from backend.auth import get_current_user

router = APIRouter(prefix="/community", tags=["Community"])


#to create a post in the community forum, which can be a discussion, question, or report of a scam. 
# The post will be associated with the user who created it and can optionally link to a specific scam report if it's a report post.
@router.post("/posts")
async def create_post(data: CreatePostRequest, current_user: dict = Depends(get_current_user)):
    try:
        post_data = {
            "user_id": str(current_user.get("user_id")),
            "post_title": data.post_title,
            "content": data.content,
            "post_type": data.post_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if data.company is not None:
            post_data["company"] = data.company
        if data.domain is not None:
            post_data["domain"] = data.domain

        response = (
            supabase.table("community_posts")
            .insert(post_data)
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

# to retrieve all posts in the community forum, with optional filtering by post type (e.g., discussion, question, report) (and pagination support not yet implemented).
@router.get("/posts")
async def get_all_posts(filter: Optional[str] = None, search: Optional[str] = None):
    """Return community posts filtered by `filter`.

    Supported filters (case-insensitive):
    - Discussion / Discussions -> post_type == "discussion", ordered by created_at desc
    - Questions / Question(s) -> post_type == "question", ordered by created_at desc
    - Scam Reports / Report(s) -> post_type == "report", ordered by created_at desc
    - Recent -> all active posts ordered by created_at desc
    - Popular -> all active posts ordered by net votes (up - down)
    If no filter provided, returns recent posts.
    """

    f = filter.strip().lower() if filter and filter.strip() else None
    s = search.strip() if search and search.strip() else None

    base_query = supabase.table("community_posts").select("*, users(full_name, avatar_url), community_votes(vote_type)").eq("status", "active")

    # add optional search
    if s:
        base_query = base_query or(f"post_title.ilike.%{s}%,content.ilike.%{s}%,company.ilike.%{s}%,domain.ilike.%{s}%")

    if f in ("discussion", "discussions"):
        response = base_query.eq("post_type", "discussion").order("created_at", desc=True).execute()
        posts = response.data or []

    elif f in ("question", "questions"):
        response = base_query.eq("post_type", "question").order("created_at", desc=True).execute()
        posts = response.data or []

    elif f and ("report" in f or f in ("report", "reports", "scam reports", "scam_report", "scam_reports")):
        response = base_query.eq("post_type", "report").order("created_at", desc=True).execute()
        posts = response.data or []

    elif f == "popular":
        response = base_query.execute()
        posts = response.data or []
        for p in posts:
            net = 0
            if p.get("community_votes"):
                for v in p["community_votes"]:
                    net += v.get("vote_type", 0)
            p["net_votes"] = net
        posts.sort(key=lambda x: x.get("net_votes", 0), reverse=True)

    else:
        response = base_query.order("created_at", desc=True).execute()
        posts = response.data or []

    # return posts (may be empty) so frontend can render an empty feed instead of receiving 404
    return posts
    
    
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
async def create_comment(post_id: str, data: CreateCommentRequest, current_user: dict = Depends(get_current_user)):
    post = (
        supabase.table("community_posts")
        .select("post_id")
        .eq("post_id", post_id)
        .execute()
    )

    if not post.data:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    response = (
        supabase.table("community_comments")
        .insert({
            "user_id": str(current_user.get("user_id")),
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
    post = (
        supabase.table("community_posts")
        .select("post_id")
        .eq("post_id", post_id)
        .execute()
    )

    if not post.data:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    response=(
        supabase.table("community_comments")
        .select("*, users(full_name, avatar_url)")
        .eq("post_id", post_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []


#vote on a post, allowing users to upvote or downvote posts in the community forum. 
# This will help surface valuable content and provide feedback to post creators. Users can only vote once per post, and they can change their vote if they wish.
@router.post("/posts/{post_id}/vote")
async def vote_post(post_id: str, data: VoteRequest, current_user: dict = Depends(get_current_user)):
    if data.vote_type not in [1, -1]:
        raise HTTPException(
            status_code=400,
            detail="vote_type must be 1 or -1"
        )
    user_id = str(current_user.get("user_id"))
    # Check if the user has already voted on this post
    existing_vote = (
        supabase.table("community_votes")
        .select("*")
        .eq("user_id", user_id)
        .eq("post_id", post_id)
        .execute()
    )

    if existing_vote.data:
        # If the user has already voted, update their vote
        if existing_vote.data[0]["vote_type"] == data.vote_type:
            # If the user is trying to vote the same way again, remove their vote
            response = (
                supabase.table("community_votes")
                .delete()
                .eq("user_id", user_id)
                .eq("post_id", post_id)
                .execute()
            )
        else:# if not the same vote, update to the new vote type (toggle between upvote and downvote)
            response = (
                supabase.table("community_votes")
                .update({"vote_type": data.vote_type})
                .eq("user_id", user_id)
                .eq("post_id", post_id)
                .execute()
            )
    else:
        # If the user hasn't voted yet, create a new vote
        response = (
            supabase.table("community_votes")
            .insert({
                "user_id": user_id,
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

    return {
        "message": "Vote recorded successfully",
        "vote_type": data.vote_type
        }
    
# delete a post, allowing users to remove their own posts from the community forum. 
# This will mark the post as deleted in the database, and it will no longer be visible to other users.
@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    # ensure post exists and ownership/admin check
    post_resp = (
        supabase.table("community_posts")
        .select("post_id, user_id")
        .eq("post_id", post_id)
        .execute()
    )
    if not post_resp.data:
        raise HTTPException(status_code=404, detail="Post not found")
    post = post_resp.data[0]
    owner_id = str(post.get("user_id"))
    user_id = str(current_user.get("user_id"))
    role = current_user.get("role")
    if role != "admin" and owner_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    response = (
        supabase.table("community_posts")
        .update({"status": "deleted"})
        .eq("post_id", post_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Post not found")

    return {"message": "Post deleted successfully"}

# delete a comment, allowing users to remove their own comments from the community forum. 
# This will mark the comment as deleted in the database, and it will no longer be visible to others
@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, current_user: dict = Depends(get_current_user)):
    comment_resp = (
        supabase.table("community_comments")
        .select("comment_id, user_id")
        .eq("comment_id", comment_id)
        .execute()
    )
    if not comment_resp.data:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment = comment_resp.data[0]
    owner_id = str(comment.get("user_id"))
    user_id = str(current_user.get("user_id"))
    role = current_user.get("role")
    if role != "admin" and owner_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    response = (
        supabase.table("community_comments")
        .update({"status": "deleted"})
        .eq("comment_id", comment_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Comment not found")

    return {"message": "Comment deleted successfully"}

# edit a comment, allowing users to update their comment content.
# Only supplied fields will be updated.
@router.put("/comments/{comment_id}")
async def edit_comment(comment_id: str, data: UpdateCommentRequest, current_user: dict = Depends(get_current_user)):
    comment = (
        supabase.table("community_comments")
        .select("comment_id")
        .eq("comment_id", comment_id)
        .execute()
    )

    if not comment.data:
        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )

    # enforce ownership unless admin
    owner_resp = (
        supabase.table("community_comments")
        .select("user_id")
        .eq("comment_id", comment_id)
        .execute()
    )
    owner_id = str(owner_resp.data[0].get("user_id")) if owner_resp.data else None
    user_id = str(current_user.get("user_id"))
    role = current_user.get("role")
    if role != "admin" and owner_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_fields = {
        key: value
        for key, value in data.model_dump(exclude_unset=True).items()
        if value is not None and key != "user_id"
    }

    if not updated_fields:
        raise HTTPException(
            status_code=400,
            detail="No update fields provided"
        )

    # #updated_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("community_comments")
        .update(updated_fields)
        .eq("comment_id", comment_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )

    return {
        "message": "Comment updated successfully",
        "comment": response.data[0]
    }

# edit a post, allowing users to update one or more fields of their posts in the community forum.
# Only the supplied fields will be updated; unspecified fields remain unchanged.
@router.put("/posts/{post_id}")
async def edit_post(post_id: str, data: UpdatePostRequest, current_user: dict = Depends(get_current_user)):
    post = (
        supabase.table("community_posts")
        .select("post_id")
        .eq("post_id", post_id)
        .execute()
    )

    if not post.data:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    # enforce ownership unless admin
    owner_resp = (
        supabase.table("community_posts")
        .select("user_id")
        .eq("post_id", post_id)
        .execute()
    )
    owner_id = str(owner_resp.data[0].get("user_id")) if owner_resp.data else None
    user_id = str(current_user.get("user_id"))
    role = current_user.get("role")
    if role != "admin" and owner_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_fields = {
        key: value
        for key, value in data.model_dump(exclude_unset=True).items()
        if value is not None and key != "user_id"
    }

    if not updated_fields:
        raise HTTPException(
            status_code=400,
            detail="No update fields provided"
        )

    # updated_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("community_posts")
        .update(updated_fields)
        .eq("post_id", post_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    return {
        "message": "Post updated successfully",
        "post": response.data[0]
    }
    
    
# get vote statistics 

@router.get("/posts/{post_id}/votes")
async def get_post_votes(post_id: str):
    # confirm post exists
    post = (
        supabase.table("community_posts")
        .select("post_id")
        .eq("post_id", post_id)
        .execute()
    )

    if not post.data:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    up_count = (
        supabase.table("community_votes")
        .select("vote_type")
        .eq("post_id", post_id)
        .eq("vote_type", 1)
        .execute()
    )

    down_count = (
        supabase.table("community_votes")
        .select("vote_type")
        .eq("post_id", post_id)
        .eq("vote_type", -1)
        .execute()
    )

    up_count = len(up_count.data) if up_count.data else 0
    down_count = len(down_count.data) if down_count.data else 0
    net_votes = up_count - down_count

    return {
        "post_id": post_id,
        "upvotes": up_count,
        "downvotes": down_count,
        "net_votes": net_votes
    }


