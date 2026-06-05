# backend/routes/analyze.py
from fastapi import APIRouter, Depends
from backend.auth import get_current_user

router = APIRouter()

# This route is defined in jobs.py (analyze_job function)
# This file is kept for structure - the actual analyze function is in jobs.py