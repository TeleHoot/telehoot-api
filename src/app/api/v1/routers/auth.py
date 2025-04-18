import hmac

from fastapi import APIRouter, HTTPException
from jose import jwt

from src import core

router = APIRouter(prefix="/auth", tags=["auth"])
settings = core.config.get_settings()


def has_correct_hash(telegram_data: core.schemas.oauth.TelegramAuth) -> bool:
    expected_hash = telegram_data.hash

    sorted_params = sorted(
        f"{x}={y}" for x, y in telegram_data.model_dump().items() if x != "hash"
    )
    data_check_bytes = "\n".join(sorted_params).encode()
    computed_hash = hmac.new(
        settings.TG.BOT_SECRET, data_check_bytes, settings.TG.ALGORITHM
    ).hexdigest()

    return hmac.compare_digest(computed_hash, expected_hash)


@router.post("/token")
def get_token(telegram_data: core.schemas.oauth.TelegramAuth):
    if not has_correct_hash(telegram_data):
        raise HTTPException(401, detail="Authentication failed")

    user_id = 1
    return jwt.encode({"user_id": user_id}, settings.SECRET_KEY, algorithm="HS256")
