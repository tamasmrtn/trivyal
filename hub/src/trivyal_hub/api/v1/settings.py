"""Settings endpoints for notification configuration."""

from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import NotificationSettings, _utcnow
from trivyal_hub.db.session import get_session

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_auth)])


class SettingsResponse(BaseModel):
    webhook_url: str | None
    webhook_type: str | None
    notify_on_critical: bool
    notify_on_high: bool


class SettingsUpdate(BaseModel):
    webhook_url: str | None = None
    webhook_type: str | None = None
    notify_on_critical: bool | None = None
    notify_on_high: bool | None = None


async def _get_or_create_settings(session: AsyncSession) -> NotificationSettings:
    result = (await session.execute(select(NotificationSettings))).scalar_one_or_none()
    if not result:
        result = NotificationSettings()
        session.add(result)
        await session.commit()
        await session.refresh(result)
    return result


@router.get("", response_model=SettingsResponse)
async def get_settings(session: AsyncSession = Depends(get_session)):
    ns = await _get_or_create_settings(session)
    return SettingsResponse.model_validate(ns, from_attributes=True)


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    session: AsyncSession = Depends(get_session),
):
    ns = await _get_or_create_settings(session)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ns, key, value)
    ns.updated_at = _utcnow()
    session.add(ns)
    await session.commit()
    await session.refresh(ns)
    return SettingsResponse.model_validate(ns, from_attributes=True)
