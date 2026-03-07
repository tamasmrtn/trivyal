"""Request/response models for misconfiguration endpoints."""

from datetime import datetime

from pydantic import BaseModel

from trivyal_hub.db.models import MisconfigStatus, Severity


class MisconfigFindingResponse(BaseModel):
    id: str
    container_id: str
    container_name: str | None
    image_name: str | None
    check_id: str
    severity: Severity
    title: str
    fix_guideline: str
    status: MisconfigStatus
    first_seen: datetime
    last_seen: datetime


class MisconfigFindingUpdate(BaseModel):
    status: MisconfigStatus
