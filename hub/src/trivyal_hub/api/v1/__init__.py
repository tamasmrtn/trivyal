"""v1 API router — aggregates all sub-routers."""

from fastapi import APIRouter

from trivyal_hub.api.v1.agents import router as agents_router
from trivyal_hub.api.v1.auth import router as auth_router
from trivyal_hub.api.v1.dashboard import router as dashboard_router
from trivyal_hub.api.v1.findings import router as findings_router
from trivyal_hub.api.v1.hub import router as hub_router
from trivyal_hub.api.v1.images import router as images_router
from trivyal_hub.api.v1.insights import router as insights_router
from trivyal_hub.api.v1.misconfigurations import router as misconfigs_router
from trivyal_hub.api.v1.scans import router as scans_router
from trivyal_hub.api.v1.settings import router as settings_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(hub_router)
router.include_router(agents_router)
router.include_router(scans_router)
router.include_router(findings_router)
router.include_router(misconfigs_router)
router.include_router(images_router)
router.include_router(dashboard_router)
router.include_router(settings_router)
router.include_router(insights_router)
