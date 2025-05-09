import json
import logging
from urllib.parse import parse_qsl

from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from src import core
from src.app import models, schemas, services

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

    async def auth_widget_user(
        self, uow: core.UnitOfWork, telegram_data: schemas.users.TelegramAuth
    ) -> schemas.auth.Token:
        if not self.check_correct_hash_widget(telegram_data):
            raise core.services.exceptions.AuthenticationError("Invalid hash")

        user = await self._get_or_create_user_with_organization(uow, telegram_data)
        token = self.encode_token({"user_id": str(user.id)})
        return schemas.auth.Token(access_token=token)

    async def auth_tma_user(self, uow: core.UnitOfWork, init_data: str) -> schemas.auth.Token:
        if not self.check_correct_hash_tma(init_data):
            raise core.services.exceptions.AuthenticationError("Invalid initData")

        parsed_data = dict(parse_qsl(init_data))

        user_data = json.loads(parsed_data["user"])

        telegram_auth_data = {
            **user_data,
            "auth_date": parsed_data.get("auth_date"),
            "hash": parsed_data.get("hash"),
        }

        filtered_data = {
            k: v
            for k, v in telegram_auth_data.items()
            if v is not None and (not isinstance(v, str) or len(v) > 0)
        }

        telegram_data = schemas.users.TelegramAuth.model_validate(filtered_data)

        user = await self._get_or_create_user_with_organization(uow, telegram_data)
        token = self.encode_token({"user_id": str(user.id)})
        return schemas.auth.Token(access_token=token)

    async def _get_or_create_user_with_organization(
        self, uow: core.UnitOfWork, telegram_data: schemas.users.TelegramAuth
    ) -> models.User:
        try:
            return await self.users_service.read_by_telegram_id(uow, telegram_data.id)
        except core.services.exceptions.EntityNotFoundError:
            user = await self.users_service.create(
                uow,
                schemas.users.Create.model_validate(telegram_data.model_dump()),
            )
            organization = await self.organizations_service.create(
                uow,
                schemas.organizations.Create(name=telegram_data.username.capitalize()),
            )
            await self.memberships_service.create(
                uow,
                schemas.memberships.Create(
                    organization_id=organization.id,
                    user_id=user.id,
                    role=models.UserRoles.OWNER,
                    status=models.MembershipStatuses.APPROVED,
                ),
            )
            return user

    @core.utils.decorators.log_operation
    async def read_user_by_token(self, uow: core.UnitOfWork, token: str) -> schemas.users.Read:
        user_data = self.decode_token(token)
        return await self.users_service.read_by_id(uow, user_data["user_id"])

    def check_correct_hash_widget(self, telegram_data: schemas.users.TelegramAuth) -> bool:
        data = telegram_data.model_dump(exclude={"hash"}, exclude_unset=True, by_alias=False)

        expected_hash = telegram_data.hash
        data_check_string = self.prepare_data_check_string(data)

        return settings.TG.verify_hash(data_check_string, expected_hash, "widget")

    def check_correct_hash_tma(self, telegram_data: str) -> bool:
        parsed_data = dict(parse_qsl(telegram_data))

        if "hash" not in parsed_data:
            return False

        received_hash = parsed_data.pop("hash")
        data_check_string = self.prepare_data_check_string(parsed_data)

        return settings.TG.verify_hash(data_check_string, received_hash, "mini_app")

    @staticmethod
    def prepare_data_check_string(data: dict) -> str:
        return "\n".join(f"{key}={value}" for key, value in sorted(data.items()))

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
        except JWTError:
            raise core.services.exceptions.AuthenticationError("Invalid credentials") from None

    @staticmethod
    def encode_token(data: dict) -> str:
        return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")
