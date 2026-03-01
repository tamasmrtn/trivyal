"""Dashboard summary endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import Agent, AgentStatus, Finding, FindingStatus, Severity
from trivyal_hub.db.session import get_session

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_auth)])


class SeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    unknown: int = 0


class AgentStatusCounts(BaseModel):
    online: int = 0
    offline: int = 0
    scanning: int = 0


class DashboardSummary(BaseModel):
    severity_counts: SeverityCounts
    agent_status_counts: AgentStatusCounts
    total_findings: int
    total_agents: int


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(session: AsyncSession = Depends(get_session)):
    # Severity counts for active findings only
    sev_rows = (
        await session.execute(
            select(Finding.severity, func.count())
            .where(Finding.status == FindingStatus.ACTIVE)
            .group_by(Finding.severity)
        )
    ).all()
    sev = {row[0]: row[1] for row in sev_rows}
    severity_counts = SeverityCounts(
        critical=sev.get(Severity.CRITICAL, 0),
        high=sev.get(Severity.HIGH, 0),
        medium=sev.get(Severity.MEDIUM, 0),
        low=sev.get(Severity.LOW, 0),
        unknown=sev.get(Severity.UNKNOWN, 0),
    )

    # Agent status counts
    agent_rows = (await session.execute(select(Agent.status, func.count()).group_by(Agent.status))).all()
    agent_map = {row[0]: row[1] for row in agent_rows}
    agent_status_counts = AgentStatusCounts(
        online=agent_map.get(AgentStatus.ONLINE, 0),
        offline=agent_map.get(AgentStatus.OFFLINE, 0),
        scanning=agent_map.get(AgentStatus.SCANNING, 0),
    )

    total_findings = (
        await session.execute(select(func.count()).select_from(Finding).where(Finding.status == FindingStatus.ACTIVE))
    ).scalar_one()

    total_agents = (await session.execute(select(func.count()).select_from(Agent))).scalar_one()

    return DashboardSummary(
        severity_counts=severity_counts,
        agent_status_counts=agent_status_counts,
        total_findings=total_findings,
        total_agents=total_agents,
    )
