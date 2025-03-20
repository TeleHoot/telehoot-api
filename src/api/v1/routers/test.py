from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["test"])


@router.post("/test")
async def test_api():
    return True
