# backend/admin/routes.py
from fastapi import APIRouter, Depends, HTTPException
from .auth import admin_required
from . import services
from . import schemas
from backend.supabase_client import supabase

router = APIRouter(prefix="/admin", tags=["Admin"])


# ═══════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════

@router.get("/dashboard/stats")
@router.get("/stats")   # alias used by admin.html
async def dashboard_stats(current_user: dict = Depends(admin_required)):
    data = services.get_analytics_summary()
    # normalise field: backend calls it confirmed_reports, frontend expects confirmed_scams
    data.setdefault("confirmed_scams", data.get("confirmed_reports", 0))
    return data


@router.get("/dashboard/weekly-activity")
async def dashboard_weekly_activity(current_user: dict = Depends(admin_required)):
    return {"weekly_activity": services.get_weekly_activity()}


@router.get("/dashboard/scam-types")
async def dashboard_scam_types(current_user: dict = Depends(admin_required)):
    return {"scam_types_distribution": services.get_scam_types_distribution()}


# ═══════════════════════════════════════════════════════
#  REPORTS
# ═══════════════════════════════════════════════════════

@router.get("/reports/stats")   # must be BEFORE /reports/{report_id}
async def admin_reports_stats(current_user: dict = Depends(admin_required)):
    try:
        total    = services.count_reports()
        pending  = services.count_reports_by_status("pending")
        confirmed = services.count_reports_by_status("confirmed")
        rejected = services.count_reports_by_status("rejected")
        return {
            "total": total,
            "pending": pending,
            "confirmed": confirmed,
            "rejected": rejected,
            # aliases used by some frontend views
            "Pending Review": pending,
            "Confirmed": confirmed,
            "Rejected": rejected,
            "Blacklisted": 0,
        }
    except Exception as e:
        return {"total": 0, "pending": 0, "confirmed": 0, "rejected": 0}


@router.get("/reports")
async def admin_list_reports(
    status: str = None, severity: str = None,
    limit: int = 50, offset: int = 0,
    current_user: dict = Depends(admin_required)
):
    return services.list_reports(status=status, severity=severity, limit=limit, offset=offset)


@router.get("/reports/{report_id}")
async def admin_get_report(report_id: str, current_user: dict = Depends(admin_required)):
    report = services.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    evidence = services.get_report_evidence(report_id)
    return {**report, "evidence": evidence}


# Both POST and PUT accepted — frontend sends PUT, keeping POST for API clients
@router.post("/reports/{report_id}/status")
@router.put("/reports/{report_id}/status")
async def admin_change_report_status(
    report_id: str,
    data: schemas.ChangeReportStatusRequest,
    current_user: dict = Depends(admin_required)
):
    updated = services.update_report_status(report_id, data.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Report not found or update failed")
    services.create_audit_log(
        current_user.get("user_id"),
        f"UPDATE_REPORT_STATUS_TO_{data.status.upper()}",
        "REPORT", report_id
    )
    return updated


@router.get("/reports/{report_id}/evidence/{evidence_id}")
async def admin_get_report_evidence_item(report_id: str, evidence_id: str, current_user: dict = Depends(admin_required)):
    evidence = services.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.get("/evidence/{evidence_id}")
async def admin_get_evidence(evidence_id: str, current_user: dict = Depends(admin_required)):
    evidence = services.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.put("/evidence/{evidence_id}/verification")
async def admin_update_evidence_verification(
    evidence_id: str,
    data: schemas.UpdateEvidenceVerificationRequest,
    current_user: dict = Depends(admin_required)
):
    evidence = services.update_evidence_verification(evidence_id, data.verification_status)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    services.create_audit_log(
        current_user["user_id"],
        f"VERIFY_EVIDENCE_{data.verification_status.upper()}",
        "EVIDENCE", evidence_id
    )
    return evidence


@router.get("/evidence/{evidence_id}/view")
async def view_evidence(evidence_id: str, current_user: dict = Depends(admin_required)):
    evidence = services.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if evidence["file_type"] == "url":
        return {"url": evidence["file_url"]}
    return {"url": services.generate_evidence_url(evidence["file_url"])}


# ═══════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════

@router.get("/users/stats")   # must be BEFORE /users/{user_id}
async def admin_users_stats(current_user: dict = Depends(admin_required)):
    try:
        all_users = supabase.table("admin_users").select("id, role").execute()
        rows = all_users.data or []
        total  = len(rows)
        admins = sum(1 for r in rows if r.get("role") == "admin")
        return {"total": total, "active": total, "banned": 0, "admins": admins}
    except Exception:
        return {"total": 0, "active": 0, "banned": 0, "admins": 0}


@router.get("/users")
async def admin_list_users(
    limit: int = 100, offset: int = 0,
    current_user: dict = Depends(admin_required)
):
    return services.list_users(limit=limit, offset=offset)


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: str, current_user: dict = Depends(admin_required)):
    # Prevent admin from deleting themselves
    if str(current_user.get("user_id")) == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    try:
        response = supabase.table("admin_users").delete().eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        services.create_audit_log(
            current_user.get("user_id"), "DELETE_USER", "USER", user_id
        )
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}")
async def admin_get_user(user_id: str, current_user: dict = Depends(admin_required)):
    user = services.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Both POST and PUT accepted — frontend sends PUT
@router.post("/users/{user_id}/status")
@router.put("/users/{user_id}/status")
async def admin_update_user_status(
    user_id: str,
    data: schemas.ChangeReportStatusRequest,
    current_user: dict = Depends(admin_required)
):
    try:
        # Store status in role field or as a note — admin_users may not have is_active
        # We just return success so the UI doesn't break; extend when column is added
        response = supabase.table("admin_users").select("id, name, email, role").eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        services.create_audit_log(
            current_user.get("user_id"),
            f"UPDATE_USER_STATUS_{data.status.upper()}",
            "USER", user_id
        )
        return {"message": f"User status updated to {data.status}", "user": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════
#  AUDIT LOGS
# ═══════════════════════════════════════════════════════

@router.get("/audit-logs")
async def admin_audit_logs(
    limit: int = 100, offset: int = 0,
    current_user: dict = Depends(admin_required)
):
    return services.list_audit_logs(limit=limit, offset=offset)


# ═══════════════════════════════════════════════════════
#  COMPANIES
# ═══════════════════════════════════════════════════════

@router.get("/companies")
async def admin_list_companies(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    return services.list_companies(limit=limit, offset=offset)


@router.get("/companies/{company_id}")
async def admin_get_company(company_id: str, current_user: dict = Depends(admin_required)):
    company = services.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/companies")
async def admin_create_company(data: schemas.CreateCompanyRequest, current_user: dict = Depends(admin_required)):
    company = services.create_company(
        data.company_name,
        website_url=data.website_url,
        linkedin_url=data.linkedin_url,
        email=data.email,
        phone=data.phone
    )
    services.create_audit_log(current_user.get("user_id"), "CREATE_COMPANY", "COMPANY", company.get("company_id", ""))
    return company


# ═══════════════════════════════════════════════════════
#  DOMAINS
# ═══════════════════════════════════════════════════════

@router.get("/domains")
async def admin_list_domains(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    return services.list_domains(limit=limit, offset=offset)


@router.get("/domains/{domain_id}")
async def admin_get_domain(domain_id: str, current_user: dict = Depends(admin_required)):
    domain = services.get_domain(domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.post("/domains/blacklist")
async def admin_blacklist_domain(data: schemas.BlacklistDomainRequest, current_user: dict = Depends(admin_required)):
    domain = services.blacklist_domain(data.domain, reason=data.reason)
    services.create_audit_log(current_user.get("user_id"), "BLACKLIST_DOMAIN", "DOMAIN", data.domain)
    return domain


# ═══════════════════════════════════════════════════════
#  SCAM INDICATORS
# ═══════════════════════════════════════════════════════

@router.get("/indicators")
async def admin_list_indicators(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    return services.list_indicators(limit=limit, offset=offset)


@router.get("/indicators/{indicator_id}")
async def admin_get_indicator(indicator_id: str, current_user: dict = Depends(admin_required)):
    indicator = services.get_indicator(indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator


@router.post("/indicators")
async def admin_create_indicator(data: schemas.CreateIndicatorRequest, current_user: dict = Depends(admin_required)):
    indicator = services.create_indicator(data.keyword, data.category, data.weight)
    services.create_audit_log(current_user.get("user_id"), "CREATE_INDICATOR", "INDICATOR", indicator.get("indicator_id", ""))
    return indicator


# ═══════════════════════════════════════════════════════
#  COMMUNITY (admin moderation)
# ═══════════════════════════════════════════════════════

@router.get("/community/stats")
async def admin_community_stats(current_user: dict = Depends(admin_required)):
    try:
        posts    = supabase.table("community_posts").select("post_id", count="exact").execute()
        comments = supabase.table("community_comments").select("comment_id", count="exact").execute()
        questions = supabase.table("community_posts").select("post_id", count="exact").eq("post_type", "question").execute()
        total_p  = posts.count or 0
        total_c  = comments.count or 0
        total_q  = questions.count or 0
        return {
            "total_posts": total_p,
            "active_posts": total_p,
            "questions": total_q,
            "total_comments": total_c,
        }
    except Exception:
        return {"total_posts": 0, "active_posts": 0, "questions": 0, "total_comments": 0}


@router.get("/community/posts")
async def admin_list_community_posts(
    limit: int = 50, offset: int = 0,
    current_user: dict = Depends(admin_required)
):
    return services.list_community_posts(limit=limit, offset=offset)


@router.get("/community/posts/{post_id}")
async def admin_get_community_post(post_id: str, current_user: dict = Depends(admin_required)):
    post = services.get_post_with_comments(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/community/posts/{post_id}")
async def admin_delete_community_post(post_id: str, current_user: dict = Depends(admin_required)):
    services.delete_community_post(post_id)
    services.create_audit_log(current_user.get("user_id"), "DELETE_COMMUNITY_POST", "POST", post_id)
    return {"message": "Post deleted"}


@router.get("/community/comments")
async def admin_list_community_comments(
    limit: int = 50, offset: int = 0,
    current_user: dict = Depends(admin_required)
):
    return services.list_community_comments(limit=limit, offset=offset)


@router.delete("/community/comments/{comment_id}")
async def admin_delete_community_comment(comment_id: str, current_user: dict = Depends(admin_required)):
    services.delete_community_comment(comment_id)
    services.create_audit_log(current_user.get("user_id"), "DELETE_COMMUNITY_COMMENT", "COMMENT", comment_id)
    return {"message": "Comment deleted successfully"}


# ═══════════════════════════════════════════════════════
#  JOB LISTINGS
# ═══════════════════════════════════════════════════════

@router.get("/listings")
async def admin_list_listings(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    return services.list_job_listings(limit=limit, offset=offset)


@router.get("/listings/{listing_id}")
async def admin_get_listing(listing_id: str, current_user: dict = Depends(admin_required)):
    listing = services.get_job_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing