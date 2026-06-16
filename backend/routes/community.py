# backend/routes/community.py
from fastapi import APIRouter, HTTPException, Depends
from backend.supabase_client import supabase
from backend.schemas.community import (
    CreatePostRequest, CreateCommentRequest,
    UpdatePostRequest, UpdateCommentRequest, VoteRequest
)
from datetime import datetime, timezone
from typing import Optional
from backend.auth import get_current_user

router = APIRouter(prefix="/community", tags=["Community"])


def _enrich_posts(posts: list) -> list:
    """Attach upvotes/downvotes/net_votes counts and author_name to each post dict."""
    for p in posts:
        votes = p.pop("community_votes", []) or []
        up = sum(1 for v in votes if v.get("vote_type") == 1)
        down = sum(1 for v in votes if v.get("vote_type") == -1)
        p["upvotes"] = up
        p["downvotes"] = down
        p["net_votes"] = up - down
        # normalise author name from admin_users join
        au = p.pop("admin_users", None)
        if au:
            p["author_name"] = au.get("name") or au.get("full_name") or "Anonymous"
        else:
            p.setdefault("author_name", "Anonymous")
    return posts


# ── CREATE POST ──────────────────────────────────────────────
@router.post("/posts")
async def create_post(data: CreatePostRequest, current_user: dict = Depends(get_current_user)):
    try:
        post_data = {
            "user_id": str(current_user.get("user_id")),
            "post_title": data.post_title,
            "content": data.content,
            "post_type": data.post_type,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if data.company is not None:
            post_data["company"] = data.company
        if data.domain is not None:
            post_data["domain"] = data.domain

        response = supabase.table("community_posts").insert(post_data).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create post")

        return {"message": "Post created successfully", "post": response.data[0]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error creating post: {exc}")


# ── LIST POSTS ───────────────────────────────────────────────
@router.get("/posts")
async def get_all_posts(filter: Optional[str] = None, search: Optional[str] = None):
    """Return community posts filtered by `filter`.

    Supported filters (case-insensitive):
    - discussion / discussions  -> post_type == "discussion", ordered by created_at desc
    - question / questions      -> post_type == "question",   ordered by created_at desc
    - warning / warnings        -> post_type == "warning",    ordered by created_at desc
    - scam / report / reports / scam_report(s) -> post_type == "report", ordered by created_at desc
    - popular                   -> all active posts ordered by net_votes desc
    - recent / (no filter)      -> all active posts ordered by created_at desc
    """
    f = filter.strip().lower() if filter and filter.strip() else None
    s = search.strip() if search and search.strip() else None

    try:
        base_query = (
            supabase.table("community_posts")
            .select("*, admin_users(name), community_votes(vote_type)")
            .eq("status", "active")
        )

        if f in ("discussion", "discussions"):
            response = base_query.eq("post_type", "discussion").order("created_at", desc=True).execute()
        elif f in ("question", "questions"):
            response = base_query.eq("post_type", "question").order("created_at", desc=True).execute()
        # elif f in ("warning", "warnings"):
        #     response = base_query.eq("post_type", "warning").order("created_at", desc=True).execute()
        elif f and ("scam" in f or f in ("report", "reports", "scam_report", "scam_reports")):
            response = base_query.eq("post_type", "report").order("created_at", desc=True).execute()
        elif f == "popular":
            response = base_query.execute()
        else:
            # "recent" or no filter
            response = base_query.order("created_at", desc=True).execute()

        posts = response.data or []
        posts = _enrich_posts(posts)

        if f == "popular":
            posts.sort(key=lambda x: x.get("net_votes", 0), reverse=True)

        # apply search client-side to avoid PostgREST OR syntax issues
        if s:
            sl = s.lower()
            posts = [
                p for p in posts
                if sl in (p.get("post_title") or "").lower()
                or sl in (p.get("content") or "").lower()
                or sl in (p.get("company") or "").lower()
                or sl in (p.get("domain") or "").lower()
            ]

        return posts
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {exc}")


# ── GET SINGLE POST ──────────────────────────────────────────
@router.get("/posts/{post_id}")
async def get_post(post_id: str):
    try:
        response = (
            supabase.table("community_posts")
            .select("*, admin_users(name), community_votes(vote_type)")
            .eq("post_id", post_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Post not found")
        posts = _enrich_posts(response.data)
        return posts[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── CREATE COMMENT ───────────────────────────────────────────
@router.post("/posts/{post_id}/comments")
async def create_comment(post_id: str, data: CreateCommentRequest, current_user: dict = Depends(get_current_user)):
    post = supabase.table("community_posts").select("post_id").eq("post_id", post_id).execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Post not found")

    response = (
        supabase.table("community_comments")
        .insert({
            "user_id": str(current_user.get("user_id")),
            "post_id": post_id,
            "content": data.content,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create comment")

    return {"message": "Comment created successfully", "comment": response.data[0]}


# ── GET COMMENTS ─────────────────────────────────────────────
@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: str):
    post = supabase.table("community_posts").select("post_id").eq("post_id", post_id).execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Post not found")

    try:
        response = (
            supabase.table("community_comments")
            .select("*, admin_users(name)")
            .eq("post_id", post_id)
            .order("created_at", desc=False)
            .execute()
        )
        comments = response.data or []
        for c in comments:
            au = c.pop("admin_users", None)
            c["author_name"] = (au.get("name") if au else None) or "Anonymous"
        return comments
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── VOTE ─────────────────────────────────────────────────────
@router.post("/posts/{post_id}/vote")
async def vote_post(post_id: str, data: VoteRequest, current_user: dict = Depends(get_current_user)):
    if data.vote_type not in [1, -1]:
        raise HTTPException(status_code=400, detail="vote_type must be 1 or -1")

    user_id = str(current_user.get("user_id"))
    existing = (
        supabase.table("community_votes")
        .select("*")
        .eq("user_id", user_id)
        .eq("post_id", post_id)
        .execute()
    )

    if existing.data:
        if existing.data[0]["vote_type"] == data.vote_type:
            # same vote again — toggle off (remove)
            response = (
                supabase.table("community_votes")
                .delete()
                .eq("user_id", user_id)
                .eq("post_id", post_id)
                .execute()
            )
        else:
            # switch vote direction
            response = (
                supabase.table("community_votes")
                .update({"vote_type": data.vote_type})
                .eq("user_id", user_id)
                .eq("post_id", post_id)
                .execute()
            )
    else:
        response = (
            supabase.table("community_votes")
            .insert({
                "user_id": user_id,
                "post_id": post_id,
                "vote_type": data.vote_type,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            .execute()
        )

    return {"message": "Vote recorded", "vote_type": data.vote_type}


# ── DELETE POST ──────────────────────────────────────────────
@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post_resp = supabase.table("community_posts").select("post_id, user_id").eq("post_id", post_id).execute()
    if not post_resp.data:
        raise HTTPException(status_code=404, detail="Post not found")

    post = post_resp.data[0]
    if current_user.get("role") != "admin" and str(post.get("user_id")) != str(current_user.get("user_id")):
        raise HTTPException(status_code=403, detail="Forbidden")

    supabase.table("community_posts").update({"status": "deleted"}).eq("post_id", post_id).execute()
    return {"message": "Post deleted successfully"}


# ── DELETE COMMENT ───────────────────────────────────────────
@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, current_user: dict = Depends(get_current_user)):
    c_resp = supabase.table("community_comments").select("comment_id, user_id").eq("comment_id", comment_id).execute()
    if not c_resp.data:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment = c_resp.data[0]
    if current_user.get("role") != "admin" and str(comment.get("user_id")) != str(current_user.get("user_id")):
        raise HTTPException(status_code=403, detail="Forbidden")

    supabase.table("community_comments").update({"status": "deleted"}).eq("comment_id", comment_id).execute()
    return {"message": "Comment deleted successfully"}


# ── EDIT COMMENT ─────────────────────────────────────────────
@router.put("/comments/{comment_id}")
async def edit_comment(comment_id: str, data: UpdateCommentRequest, current_user: dict = Depends(get_current_user)):
    c_resp = supabase.table("community_comments").select("comment_id, user_id").eq("comment_id", comment_id).execute()
    if not c_resp.data:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment = c_resp.data[0]
    if current_user.get("role") != "admin" and str(comment.get("user_id")) != str(current_user.get("user_id")):
        raise HTTPException(status_code=403, detail="Forbidden")

    fields = {
        k: v for k, v in data.model_dump(exclude_unset=True).items()
        if v is not None and k != "user_id"
    }
    if not fields:
        raise HTTPException(status_code=400, detail="No update fields provided")

    response = supabase.table("community_comments").update(fields).eq("comment_id", comment_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"message": "Comment updated successfully", "comment": response.data[0]}


# ── EDIT POST ────────────────────────────────────────────────
@router.put("/posts/{post_id}")
async def edit_post(post_id: str, data: UpdatePostRequest, current_user: dict = Depends(get_current_user)):
    p_resp = supabase.table("community_posts").select("post_id, user_id").eq("post_id", post_id).execute()
    if not p_resp.data:
        raise HTTPException(status_code=404, detail="Post not found")

    post = p_resp.data[0]
    if current_user.get("role") != "admin" and str(post.get("user_id")) != str(current_user.get("user_id")):
        raise HTTPException(status_code=403, detail="Forbidden")

    fields = {
        k: v for k, v in data.model_dump(exclude_unset=True).items()
        if v is not None and k != "user_id"
    }
    if not fields:
        raise HTTPException(status_code=400, detail="No update fields provided")

    response = supabase.table("community_posts").update(fields).eq("post_id", post_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post updated successfully", "post": response.data[0]}


# ── VOTE STATS ───────────────────────────────────────────────
@router.get("/posts/{post_id}/votes")
async def get_post_votes(post_id: str):
    post = supabase.table("community_posts").select("post_id").eq("post_id", post_id).execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Post not found")

    votes = supabase.table("community_votes").select("vote_type").eq("post_id", post_id).execute()
    all_votes = votes.data or []
    up = sum(1 for v in all_votes if v.get("vote_type") == 1)
    down = sum(1 for v in all_votes if v.get("vote_type") == -1)
    return {"post_id": post_id, "upvotes": up, "downvotes": down, "net_votes": up - down}