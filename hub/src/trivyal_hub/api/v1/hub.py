"""Hub-level endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.session import get_hub_settings, get_session

router = APIRouter(prefix="/hub", tags=["hub"], dependencies=[Depends(require_auth)])


@router.get("/public-key")
async def get_public_key(session: AsyncSession = Depends(get_session)):
    hub_settings = await get_hub_settings(session)
    return {"public_key": hub_settings.public_key}
