from typing import Annotated

from fastapi import APIRouter, Depends

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/healthcheck")
async def healthcheck():
    return {"is_success": True}


FiltersQuery = Annotated[schemas.quizzes.Filters, Depends()]
SortingQuery = Annotated[schemas.quizzes.SortParams, Depends()]


@router.get("/quizzes", response_model=list[schemas.quizzes.Read], tags=["quizzes"])
async def get_quizzes(
    uow: dependencies.uow.Full,
    quizzes_service: dependencies.services.Quizzes,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.queries.Pagination,
    current_user: dependencies.permissions.ActiveUser,
):
    if not current_user.is_admin:
        filters.is_public = True

    return await quizzes_service.read_many(
        uow, filters, sorting, pagination, include_deleted=current_user.is_admin
    )
