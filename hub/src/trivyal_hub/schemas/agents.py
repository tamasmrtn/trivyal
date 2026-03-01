"""Request/response models for agent endpoints."""

from datetime import datetime

from pydantic import BaseModel

from trivyal_hub.db.models import AgentStatus


class AgentCreate(BaseModel):
    name: str


class AgentResponse(BaseModel):
    id: str
    name: str
    status: AgentStatus
    last_seen: datetime | None
    host_metadata: dict | None
    created_at: datetime


class AgentRegistered(BaseModel):
    id: str
    name: str
    token: str
    hub_public_key: str
