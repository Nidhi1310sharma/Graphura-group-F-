# backend/routes/domains.py

from fastapi import APIRouter
from backend.supabase_client import supabase

router = APIRouter(prefix="/domains", tags=["Domains"])
@router.get("/blacklisted")
async def get_blacklisted_domains(limit: int = 12):
    response = (
        supabase.table("domain_analysis")
        .select(
            "domain,status,trust_score,ssl_valid,last_checked"
        )
        .in_("status", ["blacklisted", "suspicious"])
        .limit(limit)
        .execute()
    )

    return response.data


