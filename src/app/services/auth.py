import hmac
import logging
from hashlib import sha256

from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from src import core
from src.app import models, schemas, services
from src.core.utils.decorators import log_operation

settings = core.config.get_settings()


class Authentication:
    def __init__(
        self,
    ):
        self.users_service = services.Users()
        self.organizations_service = services.Organizations()
        self.memberships_service = services.Memberships()

        self.security = HTTPBearer()

        self.context = {}
        self.logger = logging.getLogger(f"services.{self.__class__.__name__.lower()}")

    async def auth_user(
        self, uow: core.uow.UnitOfWork, telegram_data: schemas.users.TelegramAuth
    ) -> schemas.auth.Token:
        if not self.check_correct_hash(telegram_data):
           raise core.services.exceptions.AuthenticationError("Invalid hash")  # noqa: TRY003, EM101
        try:
            user = await self.users_service.read_by_telegram_id(uow, telegram_data.telegram_id)
        except core.services.exceptions.EntityNotFoundError:
            tg_data = telegram_data.model_dump(exclude={"hash"}, exclude_unset=True)
            tg_data["telegram_id"] = tg_data.pop("id")
            user = await self.users_service.create(
                uow,
                schemas.users.Create.model_validate(
                    tg_data,
                ),
            )
            organization = await self.organizations_service.create(
                uow,
                schemas.organizations.Create(name=telegram_data.telegram_username.capitalize()),
            )
            await self.memberships_service.create(
                uow,
                schemas.memberships.Create(
                    organization_id=organization.id,
                    user_id=user.id,
                    role=models.UserRoles.CREATOR,
                    status=models.MembershipStatuses.APPROVED,
                ),
            )
        token = self.encode_token({"user_id": str(user.id)})
        return schemas.auth.Token(access_token=token)

    @log_operation
    async def read_user_by_token(self, uow: core.uow.UnitOfWork, token: str) -> schemas.users.Read:
        user_data = self.decode_token(token)
        return await self.users_service.read_by_id(uow, user_data["user_id"])

    @staticmethod
    def check_correct_hash(telegram_data: schemas.users.TelegramAuth) -> bool:
        data = telegram_data.model_dump(
            exclude={"hash", "telegram_id", "telegram_username"}, exclude_none=True, exclude_unset=True
        )
        expected_hash = telegram_data.hash

        data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))

        computed_hash = hmac.new(
            settings.TG.BOT_SECRET, data_check_string.encode(), sha256
        ).hexdigest()
        return hmac.compare_digest(computed_hash, expected_hash)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
        except JWTError:
            raise core.services.exceptions.AuthenticationError("Invalid credentials") from None  # noqa: TRY003, EM101

    @staticmethod
    def encode_token(data: dict) -> str:
        return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")
