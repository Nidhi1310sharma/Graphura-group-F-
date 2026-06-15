#admin.routes.py
from fastapi import APIRouter, Depends, HTTPException
from .auth import admin_required
from . import services
from . import schemas

router = APIRouter(prefix="/admin", tags=["Admin"])

# ===== DASHBOARD =====
@router.get("/dashboard/stats")
async def dashboard_stats(current_user: dict = Depends(admin_required)):
    analytics = services.get_analytics_summary()
    return analytics

@router.get("/dashboard/weekly-activity")
async def dashboard_weekly_activity(current_user: dict = Depends(admin_required)):
    activity = services.get_weekly_activity()
    return {"weekly_activity": activity}

@router.get("/dashboard/scam-types")
async def dashboard_scam_types(current_user: dict = Depends(admin_required)):
    dist = services.get_scam_types_distribution()
    return {"scam_types_distribution": dist}


# ===== REPORTS =====
@router.get("/reports")
async def admin_list_reports(status: str = None, limit: int = 50, offset: int = 0, current_user: dict = Depends(admin_required)):
    reports = services.list_reports(status=status, limit=limit, offset=offset)
    return reports

@router.post("/reports/{report_id}/status")
async def admin_change_report_status(report_id: str, data: schemas.ChangeReportStatusRequest, current_user: dict = Depends(admin_required)):
    updated = services.update_report_status(report_id, data.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Report not found or update failed")
    admin_id = current_user.get("user_id")
    services.create_audit_log(admin_id, f"UPDATE_REPORT_STATUS_TO_{data.status.upper()}", "REPORT", report_id)
    return updated

@router.get("/evidence/{evidence_id}")
async def admin_get_evidence(
    evidence_id: str,
    current_user: dict = Depends(admin_required)
):
    evidence = services.get_evidence(evidence_id)

    if not evidence:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found"
        )

    return evidence

@router.put("/evidence/{evidence_id}/verification")
async def admin_update_evidence_verification(
    evidence_id: str,
    data: schemas.UpdateEvidenceVerificationRequest,
    current_user: dict = Depends(admin_required)
):
    evidence = services.update_evidence_verification(
        evidence_id,
        data.verification_status
    )

    if not evidence:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found"
        )

    services.create_audit_log(
        current_user["user_id"],
        f"VERIFY_EVIDENCE_{data.verification_status.upper()}",
        "EVIDENCE",
        evidence_id
    )

    return evidence

@router.get("/evidence/{evidence_id}/view")
async def view_evidence(
    evidence_id: str,
    current_user: dict = Depends(admin_required)
):
    evidence = services.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if evidence["file_type"] == "url":
        return {"url": evidence["file_url"]}
    signed_url = services.generate_evidence_url(evidence["file_url"])
    return {"url": signed_url}
    
# ===== USERS =====
@router.get("/users")
async def admin_list_users(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    users = services.list_users(limit=limit, offset=offset)
    return users

@router.get("/users/{user_id}")
async def admin_get_user(user_id: str, current_user: dict = Depends(admin_required)):
    user = services.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ===== AUDIT LOGS =====
@router.get("/audit-logs")
async def admin_list_audit_logs(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    logs = services.list_audit_logs(limit=limit, offset=offset)
    return logs

# ===== COMPANIES =====
@router.get("/companies")
async def admin_list_companies(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    companies = services.list_companies(limit=limit, offset=offset)
    return companies

@router.get("/companies/{company_id}")
async def admin_get_company(company_id: str, current_user: dict = Depends(admin_required)):
    company = services.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.post("/companies")
async def admin_create_company(data: schemas.CreateCompanyRequest, current_user: dict = Depends(admin_required)):
    company = services.create_company(data.company_name, data.website_url, data.linkedin_url, data.email, data.phone)
    if not company:
        raise HTTPException(status_code=500, detail="Failed to create company")
    admin_id = current_user.get("user_id")
    services.create_audit_log(admin_id, "CREATE_COMPANY", "COMPANY", company.get("company_id", ""))
    return company

@router.put("/companies/{company_id}")
async def admin_update_company(company_id: str, data: schemas.UpdateCompanyRequest, current_user: dict = Depends(admin_required)):
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    company = services.update_company(company_id, **update_fields)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    admin_id = current_user.get("user_id")
    services.create_audit_log(admin_id, "UPDATE_COMPANY", "COMPANY", company_id)
    return company

@router.delete("/companies/{company_id}")
async def admin_delete_company(company_id: str, current_user: dict = Depends(admin_required)):
    success = services.delete_company(company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    admin_id = current_user.get("user_id")
    services.create_audit_log(admin_id, "DELETE_COMPANY", "COMPANY", company_id)
    return {"message": "Company deleted successfully"}

# ===== DOMAINS =====
@router.get("/domains")
async def admin_list_domains(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    domains = services.list_domains(limit=limit, offset=offset)
    return domains

@router.get("/domains/{domain_id}")
async def admin_get_domain(domain_id: str, current_user: dict = Depends(admin_required)):
    domain = services.get_domain(domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain

@router.post("/domains/blacklist")
async def admin_blacklist_domain(data: schemas.BlacklistDomainRequest, current_user: dict = Depends(admin_required)):
    domain = services.blacklist_domain(data.domain, data.reason)
    if not domain:
        raise HTTPException(status_code=500, detail="Failed to blacklist domain")
    admin_id = current_user.get("user_id")
    services.create_audit_log(admin_id, "BLACKLIST_DOMAIN", "DOMAIN", domain.get("domain_id", ""))
    return domain

@router.put("/domains/{domain_id}/status")
async def admin_update_domain_status(domain_id: str, status: str, current_user: dict = Depends(admin_required)):
    domain = services.update_domain_status(domain_id, status)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    admin_id = current_user.get("user_id")
    services.create_audit_log(admin_id, f"UPDATE_DOMAIN_STATUS_TO_{status.upper()}", "DOMAIN", domain_id)
    return domain

# # ===== SCAM INDICATORS =====
# @router.get("/indicators")
# async def admin_list_indicators(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
#     indicators = services.list_indicators(limit=limit, offset=offset)
#     return indicators

# @router.get("/indicators/{indicator_id}")
# async def admin_get_indicator(indicator_id: str, current_user: dict = Depends(admin_required)):
#     indicator = services.get_indicator(indicator_id)
#     if not indicator:
#         raise HTTPException(status_code=404, detail="Indicator not found")
#     return indicator

# @router.post("/indicators")
# async def admin_create_indicator(data: schemas.CreateIndicatorRequest, current_user: dict = Depends(admin_required)):
#     indicator = services.create_indicator(data.keyword, data.category, data.weight)
#     if not indicator:
#         raise HTTPException(status_code=500, detail="Failed to create indicator")
#     admin_id = current_user.get("user_id")
#     services.create_audit_log(admin_id, "CREATE_INDICATOR", "INDICATOR", indicator.get("indicator_id", ""))
#     return indicator

# @router.put("/indicators/{indicator_id}")
# async def admin_update_indicator(indicator_id: str, data: schemas.UpdateIndicatorRequest, current_user: dict = Depends(admin_required)):
#     update_fields = {k: v for k, v in data.model_dump().items() if v is not None}
#     if not update_fields:
#         raise HTTPException(status_code=400, detail="No fields to update")
#     indicator = services.update_indicator(indicator_id, **update_fields)
#     if not indicator:
#         raise HTTPException(status_code=404, detail="Indicator not found")
#     admin_id = current_user.get("user_id")
#     services.create_audit_log(admin_id, "UPDATE_INDICATOR", "INDICATOR", indicator_id)
#     return indicator

# @router.delete("/indicators/{indicator_id}")
# async def admin_delete_indicator(indicator_id: str, current_user: dict = Depends(admin_required)):
#     success = services.delete_indicator(indicator_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Indicator not found")
#     admin_id = current_user.get("user_id")
#     services.create_audit_log(admin_id, "DELETE_INDICATOR", "INDICATOR", indicator_id)
#     return {"message": "Indicator deleted successfully"}

# ===== COMMUNITY MODERATION =====
@router.get("/community/posts")
async def admin_list_community_posts(limit: int = 50, offset: int = 0, current_user: dict = Depends(admin_required)):
    posts = services.list_community_posts(limit=limit, offset=offset)
    return posts

@router.get("/community/posts/{post_id}")
async def admin_get_post(
    post_id: str,
    current_user: dict = Depends(admin_required)
):
    post = services.get_post_with_comments(post_id)

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    return post

@router.get("/community/comments")
async def admin_list_community_comments(limit: int = 50, offset: int = 0, current_user: dict = Depends(admin_required)):
    comments = services.list_community_comments(limit=limit, offset=offset)
    return comments

@router.delete("/community/comments/{comment_id}")
async def admin_delete_community_comment(comment_id: str, current_user: dict = Depends(admin_required)):
    comment = services.delete_community_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    admin_id = current_user.get("user_id")
    services.create_audit_log(admin_id, "DELETE_COMMUNITY_COMMENT", "COMMUNITY_COMMENT", comment_id)
    return {"message": "Comment deleted successfully"}

# ===== JOB LISTINGS =====
@router.get("/listings")
async def admin_list_listings(limit: int = 100, offset: int = 0, current_user: dict = Depends(admin_required)):
    listings = services.list_job_listings(limit=limit, offset=offset)
    return listings

@router.get("/listings/{listing_id}")
async def admin_get_listing(listing_id: str, current_user: dict = Depends(admin_required)):
    listing = services.get_job_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
