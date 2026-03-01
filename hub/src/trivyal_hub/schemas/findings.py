"""Request/response models for finding endpoints."""

from datetime import datetime

from pydantic import BaseModel

from trivyal_hub.db.models import FindingStatus, Severity


class FindingResponse(BaseModel):
    id: str
    scan_result_id: str
    cve_id: str
    package_name: str
    installed_version: str
    fixed_version: str | None
    severity: Severity
    description: str | None
    status: FindingStatus
    container_name: str | None
    first_seen: datetime
    last_seen: datetime


class FindingUpdate(BaseModel):
    status: FindingStatus


class RiskAcceptanceCreate(BaseModel):
    reason: str
    expires_at: datetime | None = None


class RiskAcceptanceResponse(BaseModel):
    id: str
    finding_id: str
    reason: str
    accepted_by: str
    expires_at: datetime | None
    created_at: datetime
