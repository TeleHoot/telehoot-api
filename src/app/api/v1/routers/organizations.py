from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from src import core
from src.app import models, schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/organizations", tags=["organizations"])
settings = core.config.get_settings()


@router.post(
    "/",
    response_model=schemas.organizations.Read,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    organization_create: schemas.organizations.Create,
    uow: dependencies.PostgresUOW,
    org_service: dependencies.OrganizationService,
    user_org_service: dependencies.OrganizationUserService,
    current_user: dependencies.ActiveUser,
):
    org = await org_service.create(uow, organization_create)
    await user_org_service.create(
        uow,
        schemas.organizations_users.Create(
            organization_id=org.id, user_id=current_user.id, role=models.UserRoles.CREATOR
        ),
    )
    return org


@router.get("/{organization_id}", response_model=schemas.organizations.Read)
async def read_organization(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
):
    return await service.read_by_id(uow, organization_id)


@router.get("/", response_model=list[schemas.organizations.Read])
async def read_organizations(
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
    filter_query: dependencies.PageLimitQuery,
):
    return await service.read_many(uow, page=filter_query.page, limit=filter_query.limit)


@router.patch(
    "/{organization_id}",
    response_model=schemas.organizations.Read,
    dependencies=[Depends(dependencies.get_creator_user)],
)
async def update_organization(
    organization_id: UUID,
    organization_update: schemas.organizations.Update,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
):
    return await service.update_by_id(uow, organization_id, organization_update)


@router.delete(
    "/{organization_id}",
    response_model=bool,
    dependencies=[Depends(dependencies.get_creator_user)],
)
async def delete_organization(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
):
    return await service.delete_by_id(uow, organization_id)


@router.post(
    "/{organization_id}/image",
    response_model=schemas.organizations.Read,
    dependencies=[Depends(dependencies.get_creator_user)],
)
async def upload_organization_image(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="Organization image")],
):
    if not file.content_type or file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only image files are allowed. Valid types: "
            f"{', '.join(settings.ALLOWED_IMAGE_TYPES)}",
        )

    return await service.upload_image(uow, organization_id, file, background_tasks)


@router.delete(
    "/{organization_id}/image",
    response_model=schemas.organizations.Read,
    dependencies=[Depends(dependencies.get_creator_user)],
)
async def delete_organization_image(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
    background_tasks: BackgroundTasks,
):
    return await service.delete_image(uow, organization_id, background_tasks)


@router.post(
    "/users",
    response_model=schemas.organizations_users.Read,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_creator_user)],
)
async def add_user_to_organization(
    user_create: schemas.organizations_users.Create,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationUserService,
):
    return await service.create(uow, user_create)


@router.get(
    "/users/{user_id}",
    response_model=schemas.organizations_users.Read,
)
async def read_organization_user(
    user_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationUserService,
):
    return await service.read_by_id(uow, user_id)


@router.get(
    "/{organization_id}/users",
    response_model=list[schemas.organizations_users.Read],
)
async def read_organization_users(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationUserService,
    filter_query: dependencies.PageLimitQuery,
):
    return await service.read_many_by_organization(
        uow, organization_id, page=filter_query.page, limit=filter_query.limit
    )


@router.patch(
    "/users/{user_id}",
    response_model=schemas.organizations_users.Read,
    dependencies=[Depends(dependencies.get_creator_user)],
)
async def update_organization_user_role(
    user_id: UUID,
    user_update: schemas.organizations_users.Update,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationUserService,
):
    return await service.update_by_id(uow, user_id, user_update)


@router.delete(
    "/users/{user_id}",
    response_model=bool,
    dependencies=[Depends(dependencies.get_creator_user)],
)
async def remove_user_from_organization(
    user_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationUserService,
):
    return await service.delete_by_id(uow, user_id)
