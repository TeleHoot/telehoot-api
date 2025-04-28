from fastapi import APIRouter

from . import routers

router = APIRouter(prefix="/v1")
router.include_router(routers.public)
router.include_router(routers.memberships)
router.include_router(routers.organizations)
router.include_router(routers.auth)
router.include_router(routers.questions)