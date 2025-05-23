from typing import Annotated
from uuid import UUID

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, status

from src import core
from src.app import schemas
from src.app.api import dependencies

router = APIRouter(
    prefix="/organizations/{organization_id}/quizzes/{quiz_id}"
    "/sessions/{session_id}/participants/{participant_id}/answers",
    tags=["participants_answers"],
)
settings = core.config.get_settings()


@router.post(
    "",
    response_model=schemas.participant_answers.Read,
    status_code=status.HTTP_201_CREATED,
)
async def create_answer(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_id: UUID,
    answer_data: schemas.participant_answers.Create,
    uow: dependencies.uow.Full,
    answers_service: dependencies.services.ParticipantAnswers,
    participants_service: dependencies.services.Participants,
    questions_service: dependencies.services.Questions,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)
    await participants_service.read_by_id(uow, participant_id)
    await questions_service.read_by_id(uow, answer_data.question_id)

    return await answers_service.create(
        uow,
        answer_data,
        additional_data={
            "participant_id": participant_id,
        },
    )


@router.get(
    "",
    response_model=list[schemas.participant_answers.Read],
)
async def get_answers(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_id: UUID,
    uow: dependencies.uow.Full,
    answers_service: dependencies.services.ParticipantAnswers,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    query: Annotated[schemas.participant_answers.Query, Query()],
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)
    await participants_service.read_by_id(uow, participant_id)

    return await answers_service.read_many(
        uow,
        schemas.participant_answers.Filters(**(query_data := query.model_dump())),
        schemas.participant_answers.SortParams(**query_data),
        core.schemas.PaginationParams(**query_data),
        include_deleted=current_user.is_admin,
    )


@router.get(
    "/{question_id}",
    response_model=schemas.participant_answers.Read,
)
async def get_answer(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_id: UUID,
    question_id: PydanticObjectId,
    uow: dependencies.uow.Full,
    answers_service: dependencies.services.ParticipantAnswers,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
    current_user: dependencies.permissions.ActiveUser,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)
    await participants_service.read_by_id(uow, participant_id)

    return await answers_service.read_by_id(
        uow,
        entity_id={"participant_id": participant_id, "question_id": question_id},
        include_deleted=current_user.is_admin,
    )


@router.patch(
    "/{question_id}",
    response_model=schemas.participant_answers.Read,
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def update_answer(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_id: UUID,
    question_id: PydanticObjectId,
    answer_data: schemas.participant_answers.Update,
    uow: dependencies.uow.Full,
    answers_service: dependencies.services.ParticipantAnswers,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)
    await participants_service.read_by_id(uow, participant_id)

    return await answers_service.update_by_id(
        uow=uow,
        entity_id={"participant_id": participant_id, "question_id": question_id},
        update_schema=answer_data,
    )


@router.delete(
    "/{question_id}",
    dependencies=[Depends(dependencies.permissions.get_active_user)],
)
async def delete_answer(
    organization_id: UUID,
    quiz_id: UUID,
    session_id: UUID,
    participant_id: UUID,
    question_id: PydanticObjectId,
    uow: dependencies.uow.Full,
    answers_service: dependencies.services.ParticipantAnswers,
    participants_service: dependencies.services.Participants,
    sessions_service: dependencies.services.Sessions,
    quizzes_service: dependencies.services.Quizzes,
    org_service: dependencies.services.Organizations,
):
    await org_service.read_by_id(uow, organization_id)
    await quizzes_service.read_by_id(uow, quiz_id)
    await sessions_service.read_by_id(uow, session_id)
    await participants_service.read_by_id(uow, participant_id)

    return {
        "is_success": await answers_service.delete_by_id(
            uow, entity_id={"participant_id": participant_id, "question_id": question_id}
        )
    }
