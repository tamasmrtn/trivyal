"""SQLModel table definitions for the hub database."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import UniqueConstraint
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from trivyal_hub.config import settings


def _now() -> datetime:
    return datetime.now(ZoneInfo(settings.tz))


# Alias kept for any existing imports
_utcnow = _now


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


class MisconfigStatus(StrEnum):
    ACTIVE = "active"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"
    FIXED = "fixed"


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


# ── Tables ───────────────────────────────────────────────────────────────────


class HubSettings(SQLModel, table=True):
    """Singleton row (id=1) storing the hub's Ed25519 keypair."""

    id: int = Field(default=1, primary_key=True)
    public_key: str
    private_key: str


class Agent(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    name: str = Field(unique=True, index=True)
    token_hash: str
    fingerprint: str | None = None
    status: AgentStatus = Field(default=AgentStatus.OFFLINE)
    last_seen: datetime | None = None
    host_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_now)

    containers: list[Container] = Relationship(
        back_populates="agent",
        cascade_delete=True,
    )


class Container(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("agent_id", "container_name", "image_name", name="uq_container_agent_image"),)

    id: str = Field(default_factory=_new_id, primary_key=True)
    agent_id: str = Field(foreign_key="agent.id", index=True)
    image_name: str
    image_tag: str | None = None
    container_name: str | None = None
    image_digest: str | None = None
    last_scanned: datetime | None = None
    created_at: datetime = Field(default_factory=_now)

    agent: Agent = Relationship(back_populates="containers")
    scan_results: list[ScanResult] = Relationship(
        back_populates="container",
        cascade_delete=True,
    )
    misconfig_findings: list[MisconfigFinding] = Relationship(
        back_populates="container",
        cascade_delete=True,
    )


class ScanResult(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    container_id: str = Field(foreign_key="container.id", index=True)
    agent_id: str = Field(foreign_key="agent.id", index=True)
    scanned_at: datetime = Field(default_factory=_now)
    trivy_raw: dict | None = Field(default=None, sa_column=Column(JSON))
    critical_count: int = Field(default=0)
    high_count: int = Field(default=0)
    medium_count: int = Field(default=0)
    low_count: int = Field(default=0)
    unknown_count: int = Field(default=0)

    container: Container = Relationship(back_populates="scan_results")
    findings: list[Finding] = Relationship(
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
    description: str | None = None
    status: FindingStatus = Field(default=FindingStatus.ACTIVE)
    first_seen: datetime = Field(default_factory=_now)
    last_seen: datetime = Field(default_factory=_now)

    scan_result: ScanResult = Relationship(back_populates="findings")
    acceptances: list[RiskAcceptance] = Relationship(
        back_populates="finding",
        cascade_delete=True,
    )


class MisconfigFinding(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    container_id: str = Field(foreign_key="container.id", index=True)
    check_id: str = Field(index=True)
    severity: Severity
    title: str
    fix_guideline: str
    status: MisconfigStatus = Field(default=MisconfigStatus.ACTIVE)
    first_seen: datetime = Field(default_factory=_now)
    last_seen: datetime = Field(default_factory=_now)

    container: Container = Relationship(back_populates="misconfig_findings")
    acceptances: list[RiskAcceptance] = Relationship(
        back_populates="misconfig_finding",
        cascade_delete=True,
    )


class RiskAcceptance(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    finding_id: str | None = Field(default=None, foreign_key="finding.id", index=True)
    misconfig_finding_id: str | None = Field(default=None, foreign_key="misconfigfinding.id", index=True)
    reason: str
    accepted_by: str = Field(default="admin")
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)

    finding: Finding | None = Relationship(back_populates="acceptances")
    misconfig_finding: MisconfigFinding | None = Relationship(back_populates="acceptances")


class NotificationSettings(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    webhook_url: str | None = None
    webhook_type: str | None = None  # slack, discord, ntfy
    notify_on_critical: bool = Field(default=True)
    notify_on_high: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=_now)
