"""Insights analytics endpoints."""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, or_, select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import Agent, Finding, FindingStatus, ScanResult, Severity, _now
from trivyal_hub.db.session import get_session

router = APIRouter(prefix="/insights", tags=["insights"], dependencies=[Depends(require_auth)])


# ── Response schemas ──────────────────────────────────────────────────────────


class InsightsSummary(BaseModel):
    active_findings: int
    critical_high: int
    new_in_period: int
    fix_rate: float


class DayPoint(BaseModel):
    date: str
    critical: int
    high: int
    medium: int
    low: int


class TrendResponse(BaseModel):
    days: list[DayPoint]
    scan_events: list[str]


class AgentDayPoint(BaseModel):
    date: str
    total: int


class AgentTrend(BaseModel):
    agent_id: str
    name: str
    days: list[AgentDayPoint]


class AgentTrendResponse(BaseModel):
    agents: list[AgentTrend]
    scan_events: list[str]


class TopCve(BaseModel):
    cve_id: str
    severity: Severity
    containers: int
    agents: int


# ── Helpers ───────────────────────────────────────────────────────────────────


def _window_start(window: int) -> datetime:
    return _now() - timedelta(days=window)


def _day_range(window: int) -> list[date]:
    start = _window_start(window).date()
    today = _now().date()
    days = []
    current = start
    while current <= today:
        days.append(current)
        current += timedelta(days=1)
    return days


_FIXABLE_COND = Finding.fixed_version.isnot(None) & (Finding.fixed_version != "")


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/summary", response_model=InsightsSummary)
async def get_summary(
    window: int = Query(30, ge=1, le=365),
    fixable: bool | None = None,
    agent_id: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    window_start_dt = _window_start(window)

    def _agent_join(q):
        if agent_id:
            return q.join(ScanResult, Finding.scan_result_id == ScanResult.id).where(ScanResult.agent_id == agent_id)
        return q

    active_q = _agent_join(select(func.count()).select_from(Finding).where(Finding.status == FindingStatus.ACTIVE))
    if fixable:
        active_q = active_q.where(_FIXABLE_COND)
    active_findings = (await session.execute(active_q)).scalar_one()

    ch_q = _agent_join(
        select(func.count())
        .select_from(Finding)
        .where(Finding.status == FindingStatus.ACTIVE)
        .where(Finding.severity.in_([Severity.CRITICAL, Severity.HIGH]))
    )
    if fixable:
        ch_q = ch_q.where(_FIXABLE_COND)
    critical_high = (await session.execute(ch_q)).scalar_one()

    new_q = _agent_join(select(func.count()).select_from(Finding).where(Finding.first_seen >= window_start_dt))
    if fixable:
        new_q = new_q.where(_FIXABLE_COND)
    new_in_period = (await session.execute(new_q)).scalar_one()

    resolved_q = _agent_join(
        select(func.count())
        .select_from(Finding)
        .where(Finding.first_seen >= window_start_dt)
        .where(Finding.status != FindingStatus.ACTIVE)
    )
    if fixable:
        resolved_q = resolved_q.where(_FIXABLE_COND)
    resolved_in_period = (await session.execute(resolved_q)).scalar_one()

    fix_rate = (resolved_in_period / new_in_period * 100) if new_in_period > 0 else 0.0

    return InsightsSummary(
        active_findings=active_findings,
        critical_high=critical_high,
        new_in_period=new_in_period,
        fix_rate=round(fix_rate, 1),
    )


@router.get("/trend", response_model=TrendResponse)
async def get_trend(
    window: int = Query(30, ge=1, le=365),
    fixable: bool | None = None,
    agent_id: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    window_start_dt = _window_start(window)

    findings_q = (
        select(Finding.severity, Finding.status, Finding.first_seen, Finding.last_seen)
        .join(ScanResult, Finding.scan_result_id == ScanResult.id)
        .where(
            or_(
                Finding.status == FindingStatus.ACTIVE,
                Finding.last_seen >= window_start_dt,
            )
        )
    )
    if fixable:
        findings_q = findings_q.where(_FIXABLE_COND)
    if agent_id:
        findings_q = findings_q.where(ScanResult.agent_id == agent_id)
    findings_rows = (await session.execute(findings_q)).all()

    scan_events_q = (
        select(ScanResult.scanned_at)
        .where(ScanResult.scanned_at >= window_start_dt)
        .order_by(ScanResult.scanned_at.asc())
    )
    if agent_id:
        scan_events_q = scan_events_q.where(ScanResult.agent_id == agent_id)
    scan_events = (await session.execute(scan_events_q)).scalars().all()

    days = _day_range(window)
    day_points = []
    for day in days:
        counts = {s: 0 for s in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW)}
        for sev, fstatus, first_seen, last_seen in findings_rows:
            if first_seen.date() > day:
                continue
            if (fstatus == FindingStatus.ACTIVE or last_seen.date() >= day) and sev in counts:
                counts[sev] += 1
        day_points.append(
            DayPoint(
                date=day.isoformat(),
                critical=counts[Severity.CRITICAL],
                high=counts[Severity.HIGH],
                medium=counts[Severity.MEDIUM],
                low=counts[Severity.LOW],
            )
        )

    return TrendResponse(
        days=day_points,
        scan_events=[e.isoformat() for e in scan_events],
    )


@router.get("/agents/trend", response_model=AgentTrendResponse)
async def get_agents_trend(
    window: int = Query(30, ge=1, le=365),
    fixable: bool | None = None,
    agent_id: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    window_start_dt = _window_start(window)

    agents_q = select(Agent.id, Agent.name)
    if agent_id:
        agents_q = agents_q.where(Agent.id == agent_id)
    agents_rows = (await session.execute(agents_q)).all()
    if not agents_rows:
        return AgentTrendResponse(agents=[], scan_events=[])

    findings_q = (
        select(ScanResult.agent_id, Finding.status, Finding.first_seen, Finding.last_seen)
        .join(Finding, Finding.scan_result_id == ScanResult.id)
        .where(
            or_(
                Finding.status == FindingStatus.ACTIVE,
                Finding.last_seen >= window_start_dt,
            )
        )
    )
    if fixable:
        findings_q = findings_q.where(_FIXABLE_COND)
    if agent_id:
        findings_q = findings_q.where(ScanResult.agent_id == agent_id)
    findings_rows = (await session.execute(findings_q)).all()

    scan_events_q = (
        select(ScanResult.scanned_at)
        .where(ScanResult.scanned_at >= window_start_dt)
        .order_by(ScanResult.scanned_at.asc())
    )
    if agent_id:
        scan_events_q = scan_events_q.where(ScanResult.agent_id == agent_id)
    scan_events = (await session.execute(scan_events_q)).scalars().all()

    days = _day_range(window)
    agent_trends = []
    for agent_id, agent_name in agents_rows:
        agent_findings = [
            (fstatus, first_seen, last_seen) for aid, fstatus, first_seen, last_seen in findings_rows if aid == agent_id
        ]
        day_points = []
        for day in days:
            total = 0
            for fstatus, first_seen, last_seen in agent_findings:
                if first_seen.date() > day:
                    continue
                if fstatus == FindingStatus.ACTIVE or last_seen.date() >= day:
                    total += 1
            day_points.append(AgentDayPoint(date=day.isoformat(), total=total))
        agent_trends.append(AgentTrend(agent_id=agent_id, name=agent_name, days=day_points))

    return AgentTrendResponse(
        agents=agent_trends,
        scan_events=[e.isoformat() for e in scan_events],
    )


@router.get("/top-cves", response_model=list[TopCve])
async def get_top_cves(
    window: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    fixable: bool | None = None,
    agent_id: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    window_start_dt = _window_start(window)

    q = (
        select(Finding.cve_id, Finding.severity, ScanResult.container_id, ScanResult.agent_id)
        .join(ScanResult, Finding.scan_result_id == ScanResult.id)
        .where(Finding.status == FindingStatus.ACTIVE)
        .where(Finding.first_seen >= window_start_dt)
    )
    if fixable:
        q = q.where(_FIXABLE_COND)
    if agent_id:
        q = q.where(ScanResult.agent_id == agent_id)
    rows = (await session.execute(q)).all()

    cve_data: dict[str, dict] = {}
    for cve_id, severity, container_id, agent_id in rows:
        if cve_id not in cve_data:
            cve_data[cve_id] = {"severity": severity, "containers": set(), "agents": set()}
        cve_data[cve_id]["containers"].add(container_id)
        cve_data[cve_id]["agents"].add(agent_id)

    sorted_cves = sorted(cve_data.items(), key=lambda x: len(x[1]["containers"]), reverse=True)[:limit]

    return [
        TopCve(
            cve_id=cve_id,
            severity=data["severity"],
            containers=len(data["containers"]),
            agents=len(data["agents"]),
        )
        for cve_id, data in sorted_cves
    ]
