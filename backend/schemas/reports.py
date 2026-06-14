# backend/schemas/reports.py

from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class CreateReportRequest(BaseModel):
    user_id: UUID
    company_name: str
    job_title: Optional[str] = None
    description: str
    scam_type: Optional[str] = None
    severity: Optional[str] = None

class CreateEvidenceRequest(BaseModel):
    file_url: str
    file_type: str
