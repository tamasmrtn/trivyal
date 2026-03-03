"""Request/response models for scan endpoints."""

from datetime import datetime

from pydantic import BaseModel


class ScanResultResponse(BaseModel):
    id: str
    container_id: str
    agent_id: str
    agent_name: str | None
    container_name: str | None
    scanned_at: datetime
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    unknown_count: int


class ScanResultDetail(ScanResultResponse):
    trivy_raw: dict | None


class ScanTriggerResponse(BaseModel):
    job_id: str
