from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/users", tags=["users"])

FiltersQuery = Annotated[schemas.users.Filters, Depends()]
SortingQuery = Annotated[schemas.users.SortParams, Depends()]


@router.get(
    "",
    dependencies=[Depends(dependencies.permissions.get_active_user)],
    response_model=list[schemas.users.Read],
)
async def get_users(
    uow: dependencies.uow.Postgres,
    users_service: dependencies.services.Users,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.queries.Pagination,
):
    return await users_service.read_many(uow, filters, sorting, pagination)


@router.get("/me")
async def get_me(current_user: dependencies.permissions.ActiveUser):
    return current_user


@router.get(
    "/me/organizations",
    response_model=list[schemas.organizations.Read],
)
async def get_my_organizations(
    uow: dependencies.uow.Postgres,
    memberships_service: dependencies.services.Memberships,
    organizations_service: dependencies.services.Organizations,
    current_user: dependencies.permissions.ActiveUser,
    pagination: dependencies.queries.Pagination,
):
    memberships = await memberships_service.read_many(
        uow, filters=schemas.memberships.Filters(user_id=current_user.id), pagination=pagination
    )

    return [
        await organizations_service.read_by_id(uow, membership.organization.id)
        for membership in memberships
    ]


@router.get(
    "/me/memberships",
    response_model=list[schemas.memberships.Read],
)
async def get_my_memberships(
    uow: dependencies.uow.Postgres,
    memberships_service: dependencies.services.Memberships,
    current_user: dependencies.permissions.ActiveUser,
    pagination: dependencies.queries.Pagination,
):
    return await memberships_service.read_many(
        uow, filters=schemas.memberships.Filters(user_id=current_user.id), pagination=pagination
    )


@router.get(
    "/me/sessions",
    response_model=list[schemas.sessions.Read],
)
async def get_my_sessions(
    uow: dependencies.uow.Full,
    sessions_service: dependencies.services.Sessions,
    participants_service: dependencies.services.Participants,
    questions_service: dependencies.services.Questions,
    current_user: dependencies.permissions.ActiveUser,
    pagination: dependencies.queries.Pagination,
):
    user_participants = await participants_service.read_many(
        uow, schemas.participants.Filters(user_id=current_user.id), pagination=pagination
    )

    sessions = []
    for participant in user_participants:
        session = await sessions_service.read_by_id(uow, participant.session_id)
        session.quiz.questions_count = await questions_service.get_count_by_quiz_id(
            uow, session.quiz.id
        )
        sessions.append(session)

    return sessions


@router.get(
    "/{user_id}",
    dependencies=[Depends(dependencies.permissions.get_active_user)],
    response_model=schemas.users.Read,
)
async def get_user(
    user_id: UUID, uow: dependencies.uow.Postgres, users_service: dependencies.services.Users
):
    return await users_service.read_by_id(uow, user_id)
