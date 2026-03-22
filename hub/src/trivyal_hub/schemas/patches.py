"""Request/response models for patch endpoints."""

from datetime import datetime

from pydantic import BaseModel

from trivyal_hub.db.models import PatchStatus, RestartStatus


class PatchCreateRequest(BaseModel):
    agent_id: str
    container_id: str
    image_name: str


class RestartResponse(BaseModel):
    id: str
    patch_request_id: str
    container_id: str
    status: RestartStatus
    block_reason: str | None
    error_message: str | None
    requested_at: datetime
    completed_at: datetime | None
    reverted_at: datetime | None


class PatchResponse(BaseModel):
    id: str
    agent_id: str
    container_id: str
    image_name: str
    patched_tag: str | None
    status: PatchStatus
    original_finding_count: int | None
    patched_finding_count: int | None
    error_message: str | None
    requested_at: datetime
    completed_at: datetime | None
    restarts: list[RestartResponse]


class PatchSummary(BaseModel):
    total_patched: int
    findings_resolved: int
    patching_available: bool
