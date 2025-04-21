from fastapi import APIRouter

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/healthcheck")
async def healthcheck():
    return 1
