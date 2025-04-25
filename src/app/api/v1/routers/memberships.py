from uuid import UUID

from fastapi import APIRouter, Depends, status

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/memberships", tags=["memberships"])
settings = core.config.get_settings()


@router.post(
    "/",
    response_model=schemas.memberships.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def create_membership(
    membership_data: schemas.memberships.Create,
    uow: dependencies.PostgresUOW,
    memberships_service: dependencies.MembershipsService,
):
    return await memberships_service.create(uow, membership_data)


@router.get(
    "/",
    response_model=list[schemas.memberships.Read],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def get_memberships(
    uow: dependencies.PostgresUOW,
    memberships_service: dependencies.MembershipsService,
    organization_id: UUID | None = None,
    user_id: UUID | None = None,
    page: int = 1,
    limit: int = 10,
):
    return await memberships_service.read_many(uow, organization_id, user_id, page, limit)


@router.get(
    "/{organization_id}/{user_id}",
    response_model=schemas.memberships.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def get_membership(
    organization_id: UUID,
    user_id: UUID,
    uow: dependencies.PostgresUOW,
    memberships_service: dependencies.MembershipsService,
):
    return await memberships_service.read_by_id(
        uow=uow, entity_id={"organization_id": organization_id, "user_id": user_id}
    )


@router.patch(
    "/{organization_id}/{user_id}",
    response_model=schemas.memberships.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def update_membership(
    organization_id: UUID,
    user_id: UUID,
    membership_data: schemas.memberships.Update,
    uow: dependencies.PostgresUOW,
    memberships_service: dependencies.MembershipsService,
):
    return await memberships_service.update_by_id(
        uow=uow,
        entity_id={"organization_id": organization_id, "user_id": user_id},
        update_schema=membership_data,
    )


@router.delete(
    "/{organization_id}/{user_id}",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_active_user)],
)
async def delete_membership(
    organization_id: UUID,
    user_id: UUID,
    uow: dependencies.PostgresUOW,
    memberships_service: dependencies.MembershipsService,
):
    return {
        "is_success": await memberships_service.delete_by_id(
            uow=uow,
            entity_id={"organization_id": organization_id, "user_id": user_id},
        )
    }
