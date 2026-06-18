# backend/routes/reports.py

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from backend.supabase_client import supabase
from backend.auth import get_current_user
from typing import Optional, List
import os
from datetime import datetime, timezone
from uuid import uuid4
from urllib.parse import urlparse

router = APIRouter(prefix="/reports",tags=["Reports"])

# to fill record for file type in the report_evidence
def get_file_type(filename: str, content_type: str) -> str:
    lc = filename.lower()
    if lc.endswith(".pdf") or "pdf" in content_type:
        return "pdf"
    if lc.endswith((".jpg", ".jpeg", ".png")) or content_type.startswith("image"):
        return "image"
    return "file"

#to check for valid urls given in evidence
def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def cleanup_report_upload(
    report_id: str,
    uploaded_paths: List[str],
    delete_report: bool = False,
):
    bucket = supabase.storage.from_("evidence")
    if uploaded_paths:
        try:
            bucket.remove(uploaded_paths)
        except Exception:
            pass
    try:
        supabase.table("report_evidence").delete().eq("report_id", report_id).execute()
    except Exception:
        pass
    if delete_report:
        try:
            supabase.table("user_reports").delete().eq("report_id", report_id).execute()
        except Exception:
            pass
        


"""create a report of a scam company, which will be stored in the user_reports table. 
The report will be associated with the user who created it, and it will include details about the company, 
the job title (if applicable), a description of the scam, and any relevant metadata such as the type of scam. 
The report will initially be marked as "pending" for review by moderators."""

@router.post("/")
async def create_report(
    current_user: dict = Depends(get_current_user),
    company_name: str = Form(...),
    job_title: Optional[str] = Form(None),
    description: str = Form(...),
    scam_type: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    urls: Optional[str] = Form(None),
):
    # basic content validation
    COMPANY_MAX_LEN = 200
    DESCRIPTION_MIN_LEN = 20
    DESCRIPTION_MAX_LEN = 5000

    # strip inputs
    company_name = company_name.strip() if isinstance(company_name, str) else company_name
    description = description.strip() if isinstance(description, str) else description

    if not files and not urls:
        raise HTTPException(
            status_code=400,
            detail="At least one evidence item is required (file or URL)."
        )

    if not company_name or len(company_name) > COMPANY_MAX_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Company name is required and must be at most {COMPANY_MAX_LEN} characters."
        )
    if not description or len(description) < DESCRIPTION_MIN_LEN or len(description) > DESCRIPTION_MAX_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Description is required and must be between {DESCRIPTION_MIN_LEN} and {DESCRIPTION_MAX_LEN} characters."
        )
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    created_at = datetime.now(timezone.utc).isoformat()
    response = (
        supabase.table("user_reports")
        .insert({
            "user_id": str(user_id),
            "company_name": company_name,
            "job_title": job_title,
            "description": description,
            "scam_type": scam_type,
            "status": "pending",
            "created_at": created_at
        })
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=400,
            detail="Failed to create report"
        )

    report = response.data[0]
    report_id = report.get("report_id")
    # verify report_id was returned; if not attempt to delete the inserted row and raise
    if not report_id:
        try:
            supabase.table("user_reports").delete().eq("user_id", str(user_id)).eq("created_at", created_at).execute()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to create report (missing report_id)")
    evidence_records = []
    uploaded_paths: List[str] = []
    bucket = supabase.storage.from_("evidence")
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

    # URL normalization/validation/deduplication will happen inside try

    try:
        # normalize and deduplicate URLs while preserving order
        if urls and isinstance(urls, str):
            urls = [urls]

        if urls:
            seen = set()
            unique_urls: List[str] = []
            for url in urls:
                if not url or not isinstance(url, str):
                    continue
                if url in seen:
                    continue
                seen.add(url)
                unique_urls.append(url)

            # validate each unique URL
            for url in unique_urls:
                if not validate_url(url):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid evidence URL provided: {url}"
                    )
            urls = unique_urls

        if files:
            if isinstance(files, UploadFile):
                files = [files]
            for upload in files:
                file_type = get_file_type(upload.filename, upload.content_type or "")
                if file_type not in ("pdf", "image"):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported file type for {os.path.basename(upload.filename)}. Only PDF and image files are allowed."
                    )

                filename = os.path.basename(upload.filename)
                file_path = f"{report_id}/{uuid4()}_{filename}"
                file_bytes = await upload.read()
                if len(file_bytes) > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {filename} exceeds maximum size of 15 MB."
                    )

                try:
                    bucket.upload(file_path, file_bytes, {"content-type": upload.content_type})
                    print("FILENAME:", upload.filename)
                    print("CONTENT TYPE:", upload.content_type)
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to upload file {filename}: {e}"
                    )

                uploaded_paths.append(file_path)
                insert_resp = (
                    supabase.table("report_evidence")
                    .insert({
                        "report_id": report_id,
                        "file_url": file_path,
                        "file_type": file_type,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    .execute()
                )
                if not insert_resp.data:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to store evidence metadata for {upload.filename}"
                    )
                evidence_records.extend(insert_resp.data)

        if urls:
            for url in urls:
                insert_resp = (
                    supabase.table("report_evidence")
                    .insert({
                        "report_id": report_id,
                        "file_url": url,
                        "file_type": "url",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    .execute()
                )
                if not insert_resp.data:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to store evidence metadata for URL {url}"
                    )
                evidence_records.extend(insert_resp.data)

        if not evidence_records:
            raise HTTPException(
                status_code=400,
                detail="At least one evidence item is required."
            )

        return {
            "message": "Report created successfully",
            "report": report,
            "evidence_created": len(evidence_records),
        }
    except HTTPException:
        cleanup_report_upload(report_id, uploaded_paths, delete_report=True)
        raise
    except Exception as exc:
        cleanup_report_upload(report_id, uploaded_paths, delete_report=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create report with evidence: {exc}"
        )

@router.get("/my-reports")
async def get_my_reports(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    response = (
        supabase.table("user_reports")
        .select("report_id, company_name, job_title, scam_type, status, created_at")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .execute()
    )

    if not response.data:
        return []

    return response.data


# The dedicated upload endpoint for adding evidence to an existing report
# has been removed. Evidence should be supplied when creating a report
# via `POST /reports` to ensure atomic creation and consistent privacy
# handling of uploaded files.

# Alias: /reports/my → /reports/my-reports (frontend calls both)
@router.get("/my")
async def get_my_reports_alias(current_user: dict = Depends(get_current_user)):
    return await get_my_reports(current_user)


# GET /reports – public list of recent/approved reports (used by report.html sidebar)
@router.get("/")
async def list_reports(limit: int = 10, status: str = "approved"):
    try:
        query = (
            supabase.table("user_reports")
            .select("report_id, company_name, job_title, scam_type, status, created_at")
            .order("created_at", desc=True)
            .limit(limit)
        )
        if status:
            query = query.eq("status", status)
        response = query.execute()
        return response.data or []
    except Exception:
        return []


# /reports/live - returns recent reports for the live feed ticker
@router.get("/live")
async def live_reports(limit: int = 50):
    try:
        response = (
            supabase.table("user_reports")
            .select("report_id, company_name, job_title, scam_type, status, created_at")
            .in_("status", ["approved", "pending"])
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception:
        return []
