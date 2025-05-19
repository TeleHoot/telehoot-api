from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from src.app import schemas
from src.app.api.dependencies import permissions, services, uow


async def get_validated_quiz(
    organization_id: UUID,
    quiz_id: UUID,
    uow: uow.Full,
    org_service: services.Organizations,
    quiz_service: services.Quizzes,
    current_user: permissions.ActiveUser,
) -> schemas.quizzes.Read:
    await org_service.read_by_id(uow, organization_id)
    quiz = await quiz_service.read_by_id(uow, quiz_id, include_deleted=current_user.is_admin)
    if str(quiz.organization.id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz does not belong to this organization",
        )
    return quiz


async def get_validated_quiz_ws(
    organization_id: UUID,
    quiz_id: UUID,
    uow: uow.Full,
    org_service: services.Organizations,
    quiz_service: services.Quizzes,
    current_user: permissions.WsUser,
) -> schemas.quizzes.Read:
    await org_service.read_by_id(uow, organization_id)
    quiz = await quiz_service.read_by_id(uow, quiz_id, include_deleted=current_user.is_admin)
    if str(quiz.organization.id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz does not belong to this organization",
        )
    return quiz


CurrentQuiz = Annotated[schemas.quizzes.Read, Depends(get_validated_quiz)]
CurrentQuizWs = Annotated[schemas.quizzes.Read, Depends(get_validated_quiz_ws)]
