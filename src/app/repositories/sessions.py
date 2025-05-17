from uuid import UUID

from sqlalchemy import Result, desc, func, select

from src import core
from src.app import models


class Sessions(core.repositories.sqlalchemy.BaseCRUD[models.Session]):
    def __init__(self):
        super().__init__(models.Session)

    @staticmethod
    async def get_session_results(
        uow: core.UnitOfWork, session_id: UUID
    ) -> Result[tuple[models.User, int]]:
        query = (
            select(
                models.User,
                func.coalesce(func.sum(models.ParticipantAnswer.points), 0).label("total_points"),
            )
            .outerjoin(models.Participant.answers)
            .join(models.Participant.user)
            .where(models.Participant.session_id == session_id)
            .group_by(models.User.id)
            .order_by(desc("total_points"))
        )

        return await uow.postgres_session.execute(query)
