from uuid import UUID

from sqlalchemy import Result, desc, func, select

from src import core
from src.app import models


class Sessions(core.repositories.sqlalchemy.BaseCRUD[models.Session]):
    def __init__(self):
        super().__init__(models.Session)

    @staticmethod
    async def get_session_results(
        uow: core.UnitOfWork, session_id: UUID, *, include_answers: bool = False
    ) -> (
        Result[tuple[models.Participant, int]]
        | Result[tuple[models.Participant, int, models.ParticipantAnswer | None]]
    ):
        total_points_subq = (
            select(
                models.ParticipantAnswer.participant_id,
                func.sum(models.ParticipantAnswer.points).label("total_points"),
            )
            .group_by(models.ParticipantAnswer.participant_id)
            .subquery()
        )

        query = (
            select(
                models.Participant,
                func.coalesce(total_points_subq.c.total_points, 0).label("total_points"),
            )
            .outerjoin(
                total_points_subq, models.Participant.id == total_points_subq.c.participant_id
            )
            .where(models.Participant.session_id == session_id,
                   models.Participant.role != models.ParticipantRole.HOST)
        )

        if include_answers:
            query = query.add_columns(models.ParticipantAnswer).outerjoin(
                models.Participant.answers
            )

        query = query.order_by(desc(func.coalesce(total_points_subq.c.total_points, 0)))

        return await uow.postgres_session.execute(query)
