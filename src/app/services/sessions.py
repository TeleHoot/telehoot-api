import secrets
from typing import Any
from uuid import UUID

from sqlalchemy import select

from src import core
from src.app import models, repositories, schemas


class Sessions(
    core.services.BaseCRUD[
        schemas.sessions.Create,
        schemas.sessions.Read,
        schemas.sessions.Update,
        schemas.sessions.Filters,
        schemas.sessions.SortParams,
        models.Session,
    ]
):
    def __init__(self):
        self.repo = repositories.Sessions()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.sessions.Create,
            read_schema=schemas.sessions.Read,
            update_schema=schemas.sessions.Update,
            filters_schema=schemas.sessions.Filters,
        )

    async def create(
        self,
        uow: core.UnitOfWork,
        create_schema: schemas.sessions.Create,
        *,
        additional_data: dict[str, Any] | None = None,
    ) -> schemas.sessions.Read:
        max_retries = 10
        additional_data = additional_data or {}

        for _ in range(max_retries):
            code = str(secrets.SystemRandom().randrange(0, 10000)).zfill(4)

            exists = await uow.postgres_session.scalar(
                select(models.Session).filter_by(
                    join_code=code, status=models.SessionStatus.WAITING
                )
            )

            if exists:
                continue

            return await super().create(
                uow,
                create_schema,
                additional_data={
                    **additional_data,
                    "join_code": code,
                },
            )

        raise RuntimeError("Failed to generate unique join code after multiple attempts")

    async def get_session_results(
        self, uow: core.UnitOfWork, session_id: UUID
    ) -> list[schemas.sessions.SessionResult]:
        result = await self.repo.get_session_results(uow, session_id)

        return [
            schemas.sessions.SessionResult(
                user=schemas.users.Read.model_validate(row.User),
                total_points=row.total_points,
            )
            for row in result
        ]
