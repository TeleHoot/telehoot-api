from typing import Annotated
from uuid import UUID
import hmac
from jose import jwt
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo

router = APIRouter(prefix="/organizations", tags=["organizations"])
settings = core.config.get_settings()

class TelegramAuth(BaseModel):
    id: Annotated[int, Field(description="Telegram user ID")]
    first_name: Annotated[str, Field(description="Telegram user first name")]
    last_name: Annotated[str, Field(description="Telegram user last name")]
    username: Annotated[str, Field(description="Telegram username")]
    photo_url: Annotated[str, Field(description="Telegram user photo URL")]
    auth_date: Annotated[int, Field(description="Unix time when the authentication was made")]
    hash: Annotated[str, Field(description="Hash of all passed parameters, used to verify the data")]

def has_correct_hash(telegram_data: TelegramAuth) -> bool:
    expected_hash = telegram_data.hash

    sorted_params = sorted(f"{x}={y}" for x, y in telegram_data.model_dump().items() if x != "hash"))
    data_check_bytes = "\n".join(sorted_params).encode()
    computed_hash = hmac.new(settings.bot_token_hash_bytes, data_check_bytes, "sha256").hexdigest()

    return hmac.compare_digest(computed_hash, expected_hash)

@router.post("/token")
def get_token(telegram_data: TelegramAuth):
    if not has_correct_hash(telegram_data):
        raise HTTPException(401, detail="Authentication failed")
    
    token = jwt.encode({"user_id": user_id}, settings.SECRET_KEY, algorithm="HS256")