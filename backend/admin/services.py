#backend/admin/services.py
from backend.supabase_client import supabase
from typing import Optional
from datetime import datetime, timedelta, timezone

# ===== REPORTS =====
def count_reports():
    resp = supabase.table("user_reports").select("report_id", count="exact").execute()
    return resp.count if hasattr(resp, "count") else None

def count_reports_by_status(status: str):
    resp = supabase.table("user_reports").select("report_id", count="exact").eq("status", status).execute()
    return resp.count if hasattr(resp, "count") else 0

def list_reports(status: Optional[str]=None, limit: int=50, offset: int=0):
    q = supabase.table("user_reports").select("*")
    if status:
        q = q.eq("status", status)
    resp = q.order("created_at", desc=True).range(offset, offset+limit-1).execute()
    return resp.data or []

def get_report(report_id: str):
    resp = supabase.table("user_reports").select("*").eq("report_id", report_id).execute()
    return resp.data[0] if resp.data else None

def get_report_evidence(report_id: str):
    resp = (
        supabase.table("report_evidence")
        .select("*")
        .eq("report_id", report_id)
        .execute()
    )

    evidence_list = resp.data or []

    for evidence in evidence_list:

        if evidence.get("file_type") == "url":
            evidence["view_url"] = evidence["file_url"]

        else:
            signed = (
                supabase.storage
                .from_("evidence")
                .create_signed_url(
                    evidence["file_url"],
                    3600
                )
            )

            evidence["view_url"] = signed.get("signedURL")

    return evidence_list

#get single evidence
def get_evidence(evidence_id: str):
    resp = (
        supabase.table("report_evidence")
        .select("*")
        .eq("evidence_id", evidence_id)
        .execute()
    )

    return resp.data[0] if resp.data else None

def update_evidence_verification(
    evidence_id: str,
    verification_status: str
):
    resp = (
        supabase.table("report_evidence")
        .update({
            "verification_status": verification_status
        })
        .eq("evidence_id", evidence_id)
        .execute()
    )

    return resp.data[0] if resp.data else None

def update_report_status(
    report_id: str,status: str
):
    resp = (
        supabase.table("user_reports")
        .update({"status": status})
        .eq("report_id", report_id)
        .execute()
    )

    return resp.data[0] if resp.data else None

def generate_evidence_url(file_path: str):
    signed = (
        supabase.storage
        .from_("evidence")
        .create_signed_url(
            file_path,
            3600
        )
    )

    return signed.get("signedURL")

# ===== USERS =====
def list_users(limit: int=100, offset: int=0):
    resp = supabase.table("admin_users").select("id, name, email, role, created_at").range(offset, offset+limit-1).execute()
    return resp.data or []

def get_user(user_id: str):
    resp = supabase.table("admin_users").select("*").eq("id", user_id).execute()
    return resp.data[0] if resp.data else None

def count_users():
    resp = supabase.table("admin_users").select("id", count="exact").execute()
    return resp.count if hasattr(resp, "count") else 0

# ===== AUDIT LOGS =====
def list_audit_logs(
    limit: int = 100,
    offset: int = 0
):
    resp = (
        supabase.table("audit_logs")
        .select("""
            log_id,
            action,
            target_type,
            target_id,
            created_at,
            admin_users (
                id,
                name,
                email
            )
        """)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return resp.data or []

def create_audit_log(admin_id: str, action: str, target_type: str, target_id: str):
    resp = supabase.table("audit_logs").insert({
        "admin_id": admin_id,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()
    return resp.data[0] if resp.data else None

# ===== COMPANIES =====
def list_companies(limit: int=100, offset: int=0):
    resp = supabase.table("companies").select("*").range(offset, offset+limit-1).execute()
    return resp.data or []

def get_company(company_id: str):
    resp = supabase.table("companies").select("*").eq("company_id", company_id).execute()
    return resp.data[0] if resp.data else None

def create_company(company_name: str, website_url: Optional[str]=None, linkedin_url: Optional[str]=None, email: Optional[str]=None, phone: Optional[str]=None):
    resp = supabase.table("companies").insert({
        "company_name": company_name,
        "website_url": website_url,
        "linkedin_url": linkedin_url,
        "email": email,
        "phone": phone,
        "trust_score": 50,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()
    return resp.data[0] if resp.data else None

def update_company(company_id: str, **kwargs):
    resp = supabase.table("companies").update(kwargs).eq("company_id", company_id).execute()
    return resp.data[0] if resp.data else None

def delete_company(company_id: str):
    resp = supabase.table("companies").delete().eq("company_id", company_id).execute()
    return len(resp.data) > 0 if resp.data else False

# ===== DOMAINS =====
def list_domains(limit: int=100, offset: int=0):
    resp = supabase.table("domain_analysis").select("*").range(offset, offset+limit-1).execute()
    domains = resp.data or []
    for domain in domains:
        domain["reports"] = count_reports_for_domain(domain["domain"])
    return domains

def get_domain(domain_id: str):
    resp = supabase.table("domain_analysis").select("*").eq("domain_id", domain_id).execute()
    return resp.data[0] if resp.data else None

def blacklist_domain(domain: str, reason: Optional[str]=None):
    resp = supabase.table("domain_analysis").insert({
        "domain": domain,
        "trust_score": 0,
        "status": "blacklisted",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_checked": datetime.now(timezone.utc).isoformat()
    }).execute()
    return resp.data[0] if resp.data else None

def count_reports_for_domain(domain: str):
    resp = (
        supabase.table("user_reports")
        .select("report_id", count="exact")
        .ilike("description", f"%{domain}%")
        .execute()
    )

    return resp.count if hasattr(resp, "count") else 0

def update_domain_status(domain_id: str, status: str):
    resp = supabase.table("domain_analysis").update({"status": status}).eq("domain_id", domain_id).execute()
    return resp.data[0] if resp.data else None

def count_blacklisted_domains():
    resp = supabase.table("domain_analysis").select("domain_id", count="exact").eq("status", "blacklisted").execute()
    return resp.count if hasattr(resp, "count") else 0

# # ===== SCAM INDICATORS =====
# def list_indicators(limit: int=100, offset: int=0):
#     resp = supabase.table("scam_indicators").select("*").range(offset, offset+limit-1).execute()
#     return resp.data or []

# def get_indicator(indicator_id: str):
#     resp = supabase.table("scam_indicators").select("*").eq("indicator_id", indicator_id).execute()
#     return resp.data[0] if resp.data else None

# def create_indicator(keyword: str, category: str, weight: int):
#     resp = supabase.table("scam_indicators").insert({
#         "keyword": keyword,
#         "category": category,
#         "weight": weight,
#         "created_at": datetime.now(timezone.utc).isoformat()
#     }).execute()
#     return resp.data[0] if resp.data else None

# def update_indicator(indicator_id: str, **kwargs):
#     resp = supabase.table("scam_indicators").update(kwargs).eq("indicator_id", indicator_id).execute()
#     return resp.data[0] if resp.data else None

# def delete_indicator(indicator_id: str):
#     resp = supabase.table("scam_indicators").delete().eq("indicator_id", indicator_id).execute()
#     return len(resp.data) > 0 if resp.data else False

# ===== COMMUNITY MODERATION =====
def get_post_vote_count(post_id: str):
    resp = (
        supabase.table("community_votes")
        .select("vote_type")
        .eq("post_id", post_id)
        .execute()
    )

    votes = resp.data or []

    return sum(v["vote_type"] for v in votes)

def delete_community_post(post_id: str):
    resp = supabase.table("community_posts").update({"status": "deleted"}).eq("post_id", post_id).eq("status", "active").execute()
    return resp.data[0] if resp.data else None

def delete_community_comment(comment_id: str):
    resp = supabase.table("community_comments").update({"status": "deleted"}).eq("comment_id", comment_id).eq("status", "active").execute()
    return resp.data[0] if resp.data else None

def list_community_posts(limit: int=50, offset: int=0):
    resp = supabase.table("community_posts").select("*").order("created_at", desc=True).range(offset, offset+limit-1).execute()
    posts = resp.data or []
    for post in posts:
        post["net_votes"] = get_post_vote_count(
            post["post_id"])
    return resp.data or []

def list_community_comments(limit: int=50, offset: int=0):
    resp = supabase.table("community_comments").select("*").order("created_at", desc=True).range(offset, offset+limit-1).execute()
    return resp.data or []

def get_post_with_comments(post_id: str):

    post = (
        supabase.table("community_posts")
        .select("*")
        .eq("post_id", post_id)
        .execute()
    )

    if not post.data:
        return None

    comments = (
        supabase.table("community_comments")
        .select("*")
        .eq("post_id", post_id)
        .eq("status", "active")
        .order("created_at", desc=True)
        .execute()
    )

    result = post.data[0]

    result["comments"] = comments.data or []
    result["net_votes"] = get_post_vote_count(post_id)

    return result

# ===== JOB LISTINGS =====
def list_job_listings(
    limit: int = 100,
    offset: int = 0
):
    resp = (
        supabase.table("job_listings")
        .select("""
            listing_id,
            job_title,
            risk_score,
            status,
            created_at,
            companies (
                company_name
            )
        """)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return resp.data or []

def list_job_listings(
    limit: int = 100,
    offset: int = 0
):
    resp = (
        supabase.table("job_listings")
        .select("""
            listing_id,
            job_title,
            risk_score,
            status,
            created_at,
            companies (
                company_name
            )
        """)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return resp.data or []

def count_high_risk_listings():
    resp = supabase.table("job_listings").select("listing_id", count="exact").gte("risk_score", 70).execute()
    return resp.count if hasattr(resp, "count") else 0

# ===== ANALYTICS =====
def get_analytics_summary():
    pending_reports = count_reports_by_status("pending")
    confirmed_reports = count_reports_by_status("confirmed")
    community_posts = supabase.table("community_posts").select("post_id", count="exact").execute()
    community_posts_count = community_posts.count if hasattr(community_posts, "count") else 0
    high_risk_listings = count_high_risk_listings()
    blacklisted_domains = count_blacklisted_domains()
    users = count_users()
    
    return {
        "pending_reports": pending_reports,
        "confirmed_reports": confirmed_reports,
        "community_posts": community_posts_count,
        "high_risk_listings": high_risk_listings,
        "blacklisted_domains": blacklisted_domains,
        "total_users": users
    }

def get_weekly_activity():
    today = datetime.now(timezone.utc)
    week_ago = today - timedelta(days=7)
    resp = supabase.table("user_reports").select("created_at").gte("created_at", week_ago.isoformat()).execute()
    data = resp.data or []
    
    daily = {}
    for d in range(7):
        day_date = (today - timedelta(days=d)).strftime("%Y-%m-%d")
        daily[day_date] = 0
    
    for report in data:
        day = report.get("created_at", "").split("T")[0]
        if day in daily:
            daily[day] += 1
    
    return daily

def get_scam_types_distribution():
    resp = supabase.table("user_reports").select("scam_type").execute()
    data = resp.data or []
    dist = {}
    for r in data:
        st = r.get("scam_type", "unknown")
        dist[st] = dist.get(st, 0) + 1
    return dist


