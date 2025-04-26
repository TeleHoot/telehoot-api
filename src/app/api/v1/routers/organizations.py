from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.params import Query

from src import core
from src.app import models, schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/organizations", tags=["organizations"])
settings = core.config.get_settings()

OrganizationsFiltersQuery = Annotated[schemas.organizations.Filters | None, Query()]


@router.post(
    "/",
    response_model=schemas.organizations.Read,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    organization_create: schemas.organizations.Create,
    uow: dependencies.PostgresUOW,
    org_service: dependencies.OrganizationService,
    user_org_service: dependencies.MembershipsService,
    current_user: dependencies.ActiveUser,
):
    org = await org_service.create(uow, organization_create)
    await user_org_service.create(
        uow,
        schemas.memberships.Create(
            organization_id=org.id,
            user_id=current_user.id,
            role=models.UserRoles.OWNER,
            status=models.MembershipStatuses.APPROVED,
        ),
    )
    return org


@router.get("/", response_model=list[schemas.organizations.Read])
async def read_organizations(
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
    filters: OrganizationsFiltersQuery = None,
    pagination: dependencies.PaginationQuery = None,
):
    return await service.read_many(uow, filters, pagination)


@router.get("/{organization_id}", response_model=schemas.organizations.Read)
async def read_organization(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
):
    return await service.read_by_id(uow, organization_id)


@router.patch(
    "/{organization_id}",
    response_model=schemas.organizations.Read,
    dependencies=[Depends(dependencies.get_active_user)],
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
    dependencies=[Depends(dependencies.get_active_user)],
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
    dependencies=[Depends(dependencies.get_active_user)],
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
    dependencies=[Depends(dependencies.get_active_user)],
)
async def delete_organization_image(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
    background_tasks: BackgroundTasks,
):
    return await service.delete_image(uow, organization_id, background_tasks)
