"""Agent management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.core.auth import generate_token, hash_token
from trivyal_hub.db.models import Agent, AgentStatus
from trivyal_hub.db.session import get_hub_settings, get_session
from trivyal_hub.schemas.agents import AgentCreate, AgentRegistered, AgentResponse
from trivyal_hub.schemas.common import PaginatedResponse

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[Depends(require_auth)])


@router.get("", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    status_filter: AgentStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    query = select(Agent)
    count_query = select(func.count()).select_from(Agent)
    if status_filter:
        query = query.where(Agent.status == status_filter)
        count_query = count_query.where(Agent.status == status_filter)

    total = (await session.execute(count_query)).scalar_one()
    query = query.offset((page - 1) * page_size).limit(page_size)
    results = (await session.execute(query)).scalars().all()

    return PaginatedResponse(
        data=[AgentResponse.model_validate(a, from_attributes=True) for a in results],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=AgentRegistered, status_code=status.HTTP_201_CREATED)
async def register_agent(
    body: AgentCreate,
    session: AsyncSession = Depends(get_session),
):
    existing = (await session.execute(select(Agent).where(Agent.name == body.name))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent name already exists")

    token = generate_token()
    hub_settings = await get_hub_settings(session)

    agent = Agent(
        name=body.name,
        token_hash=hash_token(token),
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)

    return AgentRegistered(
        id=agent.id,
        name=agent.name,
        token=token,
        hub_public_key=hub_settings.public_key,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return AgentResponse.model_validate(agent, from_attributes=True)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    await session.delete(agent)
    await session.commit()
