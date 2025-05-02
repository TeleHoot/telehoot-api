from typing import Annotated
from uuid import UUID

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/quizzes/{quiz_id}/questions", tags=["questions"])
settings = core.config.get_settings()

FiltersQuery = Annotated[schemas.questions.Filters, Depends()]
SortingQuery = Annotated[schemas.questions.SortParams, Depends()]


@router.post(
    "/",
    response_model=schemas.questions.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def create_quiz_question(
    quiz_id: UUID,
    entity: schemas.questions.Create,
    uow: dependencies.FullUOW,
    service: dependencies.QuestionsService,
    quiz_service: dependencies.QuizzesService,
):
    quiz = await quiz_service.read_by_id(uow, quiz_id)
    if not quiz:
        raise core.services.exceptions.EntityNotFoundError("Quizzes", str(quiz_id))

    return await service.create(uow, entity, additional_data={"quiz_id": quiz_id})


@router.get(
    "/",
    response_model=list[schemas.questions.Read],
    dependencies=[Depends(dependencies.get_active_user)],
)
async def get_quiz_questions(
    quiz_id: UUID,
    uow: dependencies.MongoUOW,
    service: dependencies.QuestionsService,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.PaginationQuery,
):
    # quiz_id is a required path parameter AND it is also automatically set for the filter query
    return await service.read_many(uow, filters, sorting, pagination)


@router.get(
    "/{entity_id}",
    response_model=schemas.questions.Read,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def get_quiz_question(
    quiz_id: UUID,
    entity_id: PydanticObjectId,
    uow: dependencies.FullUOW,
    service: dependencies.QuestionsService,
    quiz_service: dependencies.QuizzesService,
):
    quiz = await quiz_service.read_by_id(uow, quiz_id)
    if not quiz:
        raise core.services.exceptions.EntityNotFoundError("Quizzes", str(quiz_id))

    question = await service.read_by_id(uow, entity_id)
    if question.quiz_id != quiz_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question doesn't belong to the quiz"
        )

    return question


@router.patch(
    "/{entity_id}",
    response_model=schemas.questions.Read,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def update_quiz_question(
    quiz_id: UUID,
    entity_id: PydanticObjectId,
    entity: schemas.questions.Update,
    uow: dependencies.FullUOW,
    service: dependencies.QuestionsService,
    quiz_service: dependencies.QuizzesService,
):
    quiz = await quiz_service.read_by_id(uow, quiz_id)
    if not quiz:
        raise core.services.exceptions.EntityNotFoundError("Quizzes", str(quiz_id))

    return await service.update_by_id(
        uow=uow,
        entity_id=entity_id,
        update_schema=entity,
    )


@router.delete(
    "/{entity_id}",
    dependencies=[Depends(dependencies.get_active_user)],
)
async def delete_quiz_question(
    quiz_id: UUID,
    entity_id: PydanticObjectId,
    uow: dependencies.FullUOW,
    service: dependencies.QuestionsService,
    quiz_service: dependencies.QuizzesService,
):
    quiz = await quiz_service.read_by_id(uow, quiz_id)
    if not quiz:
        raise core.services.exceptions.EntityNotFoundError("Quizzes", str(quiz_id))

    return {"is_success": await service.delete_by_id(uow, entity_id)}


@router.post(
    "/{question_id}/image",
    response_model=schemas.questions.Read,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def upload_organization_image(
        question_id: PydanticObjectId,
        quiz_id: UUID,
        uow: dependencies.FullUOW,
        service: dependencies.QuestionsService,
        quiz_service: dependencies.QuizzesService,
        background_tasks: BackgroundTasks,
        file: Annotated[UploadFile, File(description="Question media")],
):
    if not file.content_type or file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only image files are allowed. Valid types: "
            f"{', '.join(settings.ALLOWED_IMAGE_TYPES)}",
        )

    quiz = await quiz_service.read_by_id(uow, quiz_id)
    if not quiz:
        raise core.services.exceptions.EntityNotFoundError("Quizzes", str(quiz_id))

    return await service.upload_question_media(uow, question_id, file, background_tasks)


@router.delete(
    "/{question_id}/image",
    response_model=schemas.questions.Read,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def delete_organization_image(
        question_id: PydanticObjectId,
        quiz_id: UUID,
        uow: dependencies.FullUOW,
        service: dependencies.QuestionsService,
        quiz_service: dependencies.QuizzesService,
        background_tasks: BackgroundTasks,
):
    quiz = await quiz_service.read_by_id(uow, quiz_id)
    if not quiz:
        raise core.services.exceptions.EntityNotFoundError("Quizzes", str(quiz_id))

    return await service.delete_question_media(uow, question_id, background_tasks)
