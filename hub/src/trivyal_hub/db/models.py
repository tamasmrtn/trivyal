"""SQLModel table definitions for the hub database."""

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel, Column, JSON


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid4().hex


# ── Enums ────────────────────────────────────────────────────────────────────


class AgentStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    SCANNING = "scanning"


class FindingStatus(StrEnum):
    ACTIVE = "active"
    FIXED = "fixed"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


# ── Tables ───────────────────────────────────────────────────────────────────


class Agent(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    name: str = Field(unique=True, index=True)
    token_hash: str
    fingerprint: str | None = None
    public_key: str
    private_key: str
    status: AgentStatus = Field(default=AgentStatus.OFFLINE)
    last_seen: datetime | None = None
    host_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow)

    containers: list["Container"] = Relationship(
        back_populates="agent",
        cascade_delete=True,
    )


class Container(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    agent_id: str = Field(foreign_key="agent.id", index=True)
    image_name: str
    image_digest: str | None = None
    last_scanned: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    agent: Agent = Relationship(back_populates="containers")
    scan_results: list["ScanResult"] = Relationship(
        back_populates="container",
        cascade_delete=True,
    )


class ScanResult(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    container_id: str = Field(foreign_key="container.id", index=True)
    agent_id: str = Field(foreign_key="agent.id", index=True)
    scanned_at: datetime = Field(default_factory=_utcnow)
    trivy_raw: dict | None = Field(default=None, sa_column=Column(JSON))
    critical_count: int = Field(default=0)
    high_count: int = Field(default=0)
    medium_count: int = Field(default=0)
    low_count: int = Field(default=0)
    unknown_count: int = Field(default=0)

    container: Container = Relationship(back_populates="scan_results")
    findings: list["Finding"] = Relationship(
        back_populates="scan_result",
        cascade_delete=True,
    )


class Finding(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    scan_result_id: str = Field(foreign_key="scanresult.id", index=True)
    cve_id: str = Field(index=True)
    package_name: str
    installed_version: str
    fixed_version: str | None = None
    severity: Severity
    status: FindingStatus = Field(default=FindingStatus.ACTIVE)
    first_seen: datetime = Field(default_factory=_utcnow)
    last_seen: datetime = Field(default_factory=_utcnow)

    scan_result: ScanResult = Relationship(back_populates="findings")
    acceptances: list["RiskAcceptance"] = Relationship(
        back_populates="finding",
        cascade_delete=True,
    )


class RiskAcceptance(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    finding_id: str = Field(foreign_key="finding.id", index=True)
    reason: str
    accepted_by: str = Field(default="admin")
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    finding: Finding = Relationship(back_populates="acceptances")


class NotificationSettings(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    webhook_url: str | None = None
    webhook_type: str | None = None  # slack, discord, ntfy
    notify_on_critical: bool = Field(default=True)
    notify_on_high: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=_utcnow)
