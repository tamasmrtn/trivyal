"""Request/response models for image endpoints."""

from datetime import datetime

from pydantic import BaseModel


class SeverityBreakdown(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    unknown: int = 0


class AgentRef(BaseModel):
    id: str
    name: str
    container_id: str
    patching_available: bool = False


class ImageResponse(BaseModel):
    image_name: str
    image_tag: str | None
    image_digest: str | None
    container_count: int
    agents: list[AgentRef]
    total_cves: int
    fixable_cves: int
    severity_breakdown: SeverityBreakdown
    last_scanned: datetime | None
