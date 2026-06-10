# ============================================================
# routes/jobs.py - GET /jobs
# Browse, search, and filter the real scraped job dataset
# ============================================================

from fastapi import APIRouter, Query
from typing import Optional
import json
import os

router = APIRouter()

# Load the dataset once at startup
_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "js", "jobs_data.json")
_JOBS_CACHE = None

def _load_jobs():
    global _JOBS_CACHE
    if _JOBS_CACHE is None:
        try:
            with open(_DATA_PATH, "r", encoding="utf-8") as f:
                _JOBS_CACHE = json.load(f)
        except FileNotFoundError:
            _JOBS_CACHE = []
    return _JOBS_CACHE


@router.get("/jobs", tags=["Jobs Dataset"])
async def get_jobs(
    q:        Optional[str] = Query(None, description="Search query (title, company, location)"),
    scam:     Optional[str] = Query(None, description="Scam filter: suspect | fake | legit | none"),
    ssl:      Optional[str] = Query(None, description="SSL filter: yes | no"),
    location: Optional[str] = Query(None, description="Location filter"),
    sort:     Optional[str] = Query("default", description="Sort: title | company | date | domain_age"),
    page:     int           = Query(1, ge=1),
    page_size:int           = Query(24, ge=1, le=100),
):
    """
    Browse the real scraped job dataset with search, filter, and pagination.
    Returns paginated results with total count.
    """
    jobs = _load_jobs()

    # Filter
    result = []
    q_lower = q.lower().strip() if q else None

    for j in jobs:
        if q_lower:
            hay = f"{j.get('title','')} {j.get('company','')} {j.get('location','')}".lower()
            if q_lower not in hay:
                continue

        scam_val = j.get("scam", "") or ""
        if scam == "suspect" and "suspect" not in scam_val:
            continue
        if scam == "fake" and "fake" not in scam_val:
            continue
        if scam == "legit" and "legit" not in scam_val:
            continue
        if scam == "none" and scam_val:
            continue

        if ssl == "yes" and j.get("ssl") is not True:
            continue
        if ssl == "no" and j.get("ssl") is not False:
            continue

        if location and j.get("location") != location:
            continue

        result.append(j)

    # Sort
    if sort == "title":
        result.sort(key=lambda j: j.get("title", ""))
    elif sort == "company":
        result.sort(key=lambda j: j.get("company", ""))
    elif sort == "date":
        result.sort(key=lambda j: j.get("posted_date", ""), reverse=True)
    elif sort == "domain_age":
        result.sort(key=lambda j: j.get("domain_age") or 0, reverse=True)

    total = len(result)
    start = (page - 1) * page_size
    page_data = result[start : start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "jobs": page_data
    }


@router.get("/jobs/stats", tags=["Jobs Dataset"])
async def get_jobs_stats():
    """Return summary statistics about the job dataset."""
    jobs = _load_jobs()
    total = len(jobs)
    suspect = sum(1 for j in jobs if j.get("scam") and "suspect" in j.get("scam",""))
    fake    = sum(1 for j in jobs if j.get("scam") and "fake"    in j.get("scam",""))
    legit   = sum(1 for j in jobs if j.get("scam") and "legit"   in j.get("scam",""))
    ssl_yes = sum(1 for j in jobs if j.get("ssl") is True)

    from collections import Counter
    locs = Counter(j.get("location","") for j in jobs if j.get("location"))
    domains = Counter(j.get("domain","") for j in jobs if j.get("domain"))

    return {
        "total_jobs": total,
        "suspect_count": suspect,
        "fake_count": fake,
        "legit_count": legit,
        "ssl_verified": ssl_yes,
        "top_locations": dict(locs.most_common(10)),
        "top_domains": dict(domains.most_common(10)),
    }
