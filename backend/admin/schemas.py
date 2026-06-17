#backend/admin/schemas.py
from pydantic import BaseModel
from typing import Optional

# Report Management
class ChangeReportStatusRequest(BaseModel):
    status: str

# report filters based on pending, confirmed and rejected   
# class ReportFilter
 
class UpdateEvidenceVerificationRequest(BaseModel):
    verification_status: str

# Company Management
class CreateCompanyRequest(BaseModel):
    company_name: str
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class UpdateCompanyRequest(BaseModel):
    company_name: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    trust_score: Optional[int] = None
    status: Optional[str] = None

# Domain Management
class BlacklistDomainRequest(BaseModel):
    domain: str
    reason: Optional[str] = None

class RemoveBlacklistRequest(BaseModel):
    domain: str

# Scam Indicator Management
class CreateIndicatorRequest(BaseModel):
    keyword: str
    category: str
    weight: int

class UpdateIndicatorRequest(BaseModel):
    keyword: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[int] = None

# Community Moderation
class ModerateCommunityItemRequest(BaseModel):
    action: str  # delete, flag, approve
    reason: Optional[str] = None

# Analytics
class AnalyticsFilterParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    scam_type: Optional[str] = None
    severity: Optional[str] = None

# add admin
class CreateAdminRequest(BaseModel):
    name: str
    email: str
    password: str