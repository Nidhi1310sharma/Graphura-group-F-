# backend/routes/live_feed.py

from fastapi import APIRouter
from backend.supabase_client import supabase

router = APIRouter(prefix="/live-feed", tags=["LiveFeed"])
