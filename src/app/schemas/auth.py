from typing import Annotated

from pydantic import BaseModel, Field


class TelegramAuth(BaseModel):
    id: Annotated[int, Field(description="Telegram user ID")]
    first_name: Annotated[str, Field(description="Telegram user first name")]
    last_name: Annotated[str, Field(description="Telegram user last name")]
    username: Annotated[str, Field(description="Telegram username")]
    photo_url: Annotated[str, Field(description="Telegram user photo URL")]
    auth_date: Annotated[int, Field(description="Unix time when the authentication was made")]
    hash: Annotated[
        str, Field(description="Hash of all passed parameters, used to verify the data")
    ]
