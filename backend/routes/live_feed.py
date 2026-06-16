# backend/routes/live_feed.py

from fastapi import APIRouter
from backend.supabase_client import supabase

router = APIRouter(prefix="/live-feed", tags=["LiveFeed"])
@router.get('/feed-live')
def live_feed(limit: int = 20):
    """Live scam feed – polled every 5 seconds from frontend."""
    try:
        res = supabase.table('user_reports').select('*').eq('status','accepted').order('reported_at', desc=True).limit(limit).execute()
        return {'feed': res.data or []}
    except Exception:
        return {'feed': []}
