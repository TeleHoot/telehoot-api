import hmac
import logging

from fastapi import HTTPException, status
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
        self.organizations_users_service = services.OrganizationsUsers()

        self.security = HTTPBearer()

        self.context = {}
        self.logger = logging.getLogger(f"services.{self.__class__.__name__.lower()}")

    @log_operation
    async def auth_user(
        self, uow: core.uow.UnitOfWork, telegram_data: schemas.users.TelegramAuth
    ) -> str:
        if not self.check_correct_hash(telegram_data):
            raise HTTPException(401, detail="Authentication failed")

        try:
            user = await self.users_service.read_by_telegram_id(uow, telegram_data.telegram_id)
        except core.services.exceptions.EntityNotFoundError:
            user = await self.users_service.create(uow, telegram_data)
            organization = await self.organizations_service.create(
                uow,
                schemas.organizations.Create(name=telegram_data.telegram_username.capitalize()),
            )
            await self.organizations_users_service.create(
                uow,
                schemas.organizations_users.Create(
                    organization_id=organization.id, user_id=user.id, role=models.UserRoles.CREATOR
                ),
            )

        return self.encode_token({"user_id": user.id})

    @log_operation
    async def read_user_by_token(self, uow: core.uow.UnitOfWork, token: str) -> schemas.users.Read:
        user_data = self.decode_token(token)
        return await self.users_service.read_by_id(uow, user_data["user_id"])

    @log_operation
    @staticmethod
    def check_correct_hash(telegram_data: schemas.users.TelegramAuth) -> bool:
        expected_hash = telegram_data.hash

        sorted_params = sorted(
            f"{x}={y}" for x, y in telegram_data.model_dump().items() if x != "hash"
        )
        data_check_bytes = "\n".join(sorted_params).encode()
        computed_hash = hmac.new(
            settings.TG.BOT_SECRET, data_check_bytes, settings.TG.ALGORITHM
        ).hexdigest()

        return hmac.compare_digest(computed_hash, expected_hash)

    @log_operation
    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
        except JWTError as e:
            self.logger.exception("Invalid authentication credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            ) from e

    @log_operation
    @staticmethod
    def encode_token(data: dict) -> str:
        return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")
