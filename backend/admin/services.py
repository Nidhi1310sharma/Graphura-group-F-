# backend/admin/services.py
from backend.supabase_client import supabase
from typing import Optional
from datetime import datetime, timedelta, timezone
import csv
import io

# ===== REPORTS =====
def count_reports():
    try:
        resp = supabase.table("user_reports").select("report_id", count="exact").execute()
        return resp.count if hasattr(resp, "count") else 0
    except Exception:
        return 0

def count_reports_by_status(status: str):
    try:
        resp = supabase.table("user_reports").select("report_id", count="exact").eq("status", status).execute()
        return resp.count if hasattr(resp, "count") else 0
    except Exception:
        return 0

def list_reports(status: Optional[str]=None, severity: Optional[str]=None, limit: int=50, offset: int=0):
    try:
        q = supabase.table("user_reports").select("*")
        if status:
            q = q.eq("status", status)
        if severity:
            q = q.eq("severity", severity)
        resp = q.order("created_at", desc=True).range(offset, offset+limit-1).execute()
        return resp.data or []
    except Exception:
        return []

def get_report(report_id: str):
    try:
        resp = supabase.table("user_reports").select("*").eq("report_id", report_id).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def get_report_evidence(report_id: str):
    try:
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
                try:
                    signed = (
                        supabase.storage
                        .from_("evidence")
                        .create_signed_url(
                            evidence["file_url"],
                            3600
                        )
                    )
                    evidence["view_url"] = signed.get("signedURL")
                except Exception:
                    evidence["view_url"] = None
        return evidence_list
    except Exception:
        return []

def get_evidence(evidence_id: str):
    try:
        resp = (
            supabase.table("report_evidence")
            .select("*")
            .eq("evidence_id", evidence_id)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def update_evidence_verification(evidence_id: str, verification_status: str):
    try:
        resp = (
            supabase.table("report_evidence")
            .update({"verification_status": verification_status})
            .eq("evidence_id", evidence_id)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def update_report_status(report_id: str, status: str):
    try:
        resp = (
            supabase.table("user_reports")
            .update({"status": status})
            .eq("report_id", report_id)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def generate_evidence_url(file_path: str):
    try:
        signed = (
            supabase.storage
            .from_("evidence")
            .create_signed_url(file_path, 3600)
        )
        return signed.get("signedURL")
    except Exception:
        return None

# ===== EXPORT REPORTS CSV =====
def export_reports_csv():
    """
    Export all reports as CSV data
    Returns: CSV string or None
    """
    try:
        resp = supabase.table("user_reports").select("*").order("created_at", desc=True).execute()
        reports = resp.data or []
        
        if not reports:
            return None
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Report ID",
            "Company Name",
            "Job Title",
            "Scam Type",
            "Description",
            "Status",
            "Severity",
            "Reporter Name",
            "Reporter Email",
            "Created At"
        ])
        
        for report in reports:
            writer.writerow([
                report.get("report_id", ""),
                report.get("company_name", ""),
                report.get("job_title", ""),
                report.get("scam_type", ""),
                report.get("description", ""),
                report.get("status", ""),
                report.get("severity", ""),
                report.get("reporter_name", ""),
                report.get("reporter_email", ""),
                report.get("created_at", "")
            ])
        
        return output.getvalue()
    except Exception as e:
        print(f"[ERROR] Export CSV: {e}")
        return None

# ===== USERS =====
def list_users(limit: int=100, offset: int=0):
    try:
        resp = supabase.table("admin_users").select("id, name, email, role, created_at").range(offset, offset+limit-1).execute()
        return resp.data or []
    except Exception:
        return []

def get_user(user_id: str):
    try:
        resp = supabase.table("admin_users").select("*").eq("id", user_id).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def count_users():
    try:
        resp = supabase.table("admin_users").select("id", count="exact").execute()
        return resp.count if hasattr(resp, "count") else 0
    except Exception:
        return 0

def delete_user(user_id: str):
    try:
        check = (
            supabase.table("admin_users")
            .select("id")
            .eq("id", user_id)
            .execute()
        )

        if not check.data:
            return False

        # Delete votes
        supabase.table("community_votes") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()

        # Delete comments
        supabase.table("community_comments") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()

        # Delete posts
        posts = (
            supabase.table("community_posts")
            .select("post_id")
            .eq("user_id", user_id)
            .execute()
        )

        for post in posts.data:
            pid = post["post_id"]

            supabase.table("community_votes") \
                .delete() \
                .eq("post_id", pid) \
                .execute()

            supabase.table("community_comments") \
                .delete() \
                .eq("post_id", pid) \
                .execute()

        supabase.table("community_posts") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()

        # Delete evidence attached to reports
        reports = (
            supabase.table("user_reports")
            .select("report_id")
            .eq("user_id", user_id)
            .execute()
        )

        for report in reports.data:
            supabase.table("report_evidence") \
                .delete() \
                .eq("report_id", report["report_id"]) \
                .execute()

        # Delete reports
        supabase.table("user_reports") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()

        # Audit logs
        supabase.table("audit_logs") \
            .update({"admin_id": None}) \
            .eq("admin_id", user_id) \
            .execute()

        # Finally delete user
        resp = (
            supabase.table("admin_users")
            .delete()
            .eq("id", user_id)
            .execute()
        )

        return bool(resp.data)

    except Exception as e:
        print(f"[ERROR] Delete user {user_id}: {e}")
        return False

# ===== AUDIT LOGS =====
def list_audit_logs(limit: int = 100, offset: int = 0):
    try:
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
    except Exception:
        return []

def create_audit_log(admin_id: str, action: str, target_type: str, target_id: str):
    try:
        resp = supabase.table("audit_logs").insert({
            "admin_id": admin_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None

# ===== COMPANIES =====
def list_companies(limit: int=100, offset: int=0):
    try:
        resp = supabase.table("companies").select("*").range(offset, offset+limit-1).execute()
        return resp.data or []
    except Exception:
        return []

def get_company(company_id: str):
    try:
        resp = supabase.table("companies").select("*").eq("company_id", company_id).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def create_company(company_name: str, website_url: Optional[str]=None, linkedin_url: Optional[str]=None, email: Optional[str]=None, phone: Optional[str]=None):
    try:
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
    except Exception:
        return None

def update_company(company_id: str, **kwargs):
    try:
        resp = supabase.table("companies").update(kwargs).eq("company_id", company_id).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def delete_company(company_id: str):
    try:
        resp = supabase.table("companies").delete().eq("company_id", company_id).execute()
        return len(resp.data) > 0 if resp.data else False
    except Exception:
        return False

# ===== DOMAINS =====
def list_domains(limit: int=100, offset: int=0):
    try:
        resp = supabase.table("domain_analysis").select("*").range(offset, offset+limit-1).execute()
        domains = resp.data or []
        for domain in domains:
            domain["reports"] = count_reports_for_domain(domain.get("domain", ""))
        return domains
    except Exception:
        return []

def get_domain(domain_id: str):
    try:
        resp = supabase.table("domain_analysis").select("*").eq("domain_id", domain_id).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def blacklist_domain(domain: str, reason: Optional[str]=None):
    try:
        resp = supabase.table("domain_analysis").insert({
            "domain": domain,
            "trust_score": 0,
            "status": "blacklisted",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_checked": datetime.now(timezone.utc).isoformat()
        }).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def count_reports_for_domain(domain: str):
    try:
        resp = (
            supabase.table("user_reports")
            .select("report_id", count="exact")
            .ilike("description", f"%{domain}%")
            .execute()
        )
        return resp.count if hasattr(resp, "count") else 0
    except Exception:
        return 0

def update_domain_status(domain_id: str, status: str):
    try:
        resp = supabase.table("domain_analysis").update({"status": status}).eq("domain_id", domain_id).execute()
        return resp.data[0] if resp.data else None
    except Exception:
        return None

def count_blacklisted_domains():
    try:
        resp = supabase.table("domain_analysis").select("domain_id", count="exact").eq("status", "blacklisted").execute()
        return resp.count if hasattr(resp, "count") else 0
    except Exception:
        return 0

# ===== COMMUNITY MODERATION =====
def get_post_vote_count(post_id: str):
    try:
        resp = (
            supabase.table("community_votes")
            .select("vote_type")
            .eq("post_id", post_id)
            .execute()
        )
        votes = resp.data or []
        return sum(v.get("vote_type", 0) for v in votes)
    except Exception:
        return 0

def delete_post(post_id: str):
    try:
        # Check if post exists
        post = (
            supabase.table("community_posts")
            .select("*")
            .eq("post_id", post_id)
            .execute()
        )

        if not post.data:
            return None

        # Delete all votes for the post
        supabase.table("community_votes") \
            .delete() \
            .eq("post_id", post_id) \
            .execute()

        # Delete all comments for the post
        supabase.table("community_comments") \
            .delete() \
            .eq("post_id", post_id) \
            .execute()

        # Delete the post itself
        deleted = (
            supabase.table("community_posts")
            .delete()
            .eq("post_id", post_id)
            .execute()
        )

        return deleted.data[0] if deleted.data else None

    except Exception as e:
        print(f"[ERROR] Delete post {post_id}: {e}")
        return None

def delete_comment(comment_id: str):
    try:
        check = supabase.table("community_comments").select("comment_id").eq("comment_id", comment_id).execute()
        if not check.data:
            return None
        
        resp = supabase.table("community_comments").delete().eq("comment_id", comment_id).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        print(f"[ERROR] Delete comment {comment_id}: {e}")
        return None

def list_community_posts(limit: int=50, offset: int=0):
    try:
        resp = supabase.table("community_posts").select("*").order("created_at", desc=True).range(offset, offset+limit-1).execute()
        posts = resp.data or []
        for post in posts:
            post["net_votes"] = get_post_vote_count(post.get("post_id", ""))
        return posts
    except Exception:
        return []

def list_community_comments(limit: int=50, offset: int=0):
    try:
        resp = supabase.table("community_comments").select("*").order("created_at", desc=True).range(offset, offset+limit-1).execute()
        return resp.data or []
    except Exception:
        return []

def get_post_with_comments(post_id: str):
    try:
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
            .order("created_at", desc=True)
            .execute()
        )
        
        result = post.data[0]
        result["comments"] = comments.data or []
        result["net_votes"] = get_post_vote_count(post_id)
        
        return result
    except Exception as e:
        print(f"[ERROR] get_post_with_comments: {e}")
        return None

# ===== COMMUNITY EXPORT =====
def export_community_posts_csv():
    try:
        resp = supabase.table("community_posts").select("*").order("created_at", desc=True).execute()
        posts = resp.data or []
        
        if not posts:
            return None
        
        for post in posts:
            if post.get("user_id"):
                user = supabase.table("admin_users").select("name").eq("id", post["user_id"]).execute()
                if user.data:
                    post["author_name"] = user.data[0].get("name", "Unknown")
                else:
                    post["author_name"] = "Unknown"
            else:
                post["author_name"] = "Anonymous"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Post ID",
            "Title",
            "Author",
            "Post Type",
            "Content",
            "Created At",
            "Status"
        ])
        
        for post in posts:
            writer.writerow([
                post.get("post_id", ""),
                post.get("post_title", post.get("title", "")),
                post.get("author_name", "Unknown"),
                post.get("post_type", ""),
                post.get("content", post.get("body", "")),
                post.get("created_at", ""),
                post.get("status", "active")
            ])
        
        return output.getvalue()
    except Exception as e:
        print(f"[ERROR] Export community posts CSV: {e}")
        return None

# ===== JOB LISTINGS =====
def list_job_listings(limit: int = 100, offset: int = 0):
    try:
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
    except Exception:
        return []

def count_high_risk_listings():
    try:
        resp = supabase.table("job_listings").select("listing_id", count="exact").gte("risk_score", 70).execute()
        return resp.count if hasattr(resp, "count") else 0
    except Exception:
        return 0

# ===== ANALYTICS =====
def get_analytics_summary():
    try:
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
            "confirmed_scams": confirmed_reports,
            "community_posts": community_posts_count,
            "high_risk_listings": high_risk_listings,
            "blacklisted_domains": blacklisted_domains,
            "total_users": users
        }
    except Exception:
        return {
            "pending_reports": 0,
            "confirmed_reports": 0,
            "confirmed_scams": 0,
            "community_posts": 0,
            "high_risk_listings": 0,
            "blacklisted_domains": 0,
            "total_users": 0
        }

def get_weekly_activity():
    try:
        today = datetime.now(timezone.utc)
        week_ago = today - timedelta(days=7)
        resp = supabase.table("user_reports").select("created_at").gte("created_at", week_ago.isoformat()).execute()
        data = resp.data or []
        
        daily = {}
        for d in range(7):
            day_date = (today - timedelta(days=d)).strftime("%Y-%m-%d")
            daily[day_date] = 0
        
        for report in data:
            day = report.get("created_at", "").split("T")[0] if report.get("created_at") else None
            if day and day in daily:
                daily[day] += 1
        
        return daily
    except Exception:
        return {}

def get_scam_types_distribution():
    try:
        resp = supabase.table("user_reports").select("scam_type").execute()
        data = resp.data or []
        dist = {}
        for r in data:
            st = r.get("scam_type", "unknown")
            if st:
                st_lower = st.lower().strip()
                dist[st_lower] = dist.get(st_lower, 0) + 1
            else:
                dist["unknown"] = dist.get("unknown", 0) + 1
        return dist
    except Exception:
        return {}