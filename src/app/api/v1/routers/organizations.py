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

from src import core
from src.app import models, schemas
from src.app.api import dependencies

router = APIRouter(prefix="/organizations", tags=["organizations"])
settings = core.config.get_settings()


FiltersQuery = Annotated[schemas.organizations.Filters, Depends()]
SortingQuery = Annotated[schemas.organizations.SortParams, Depends()]


@router.post(
    "",
    response_model=schemas.organizations.Read,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    organization_create: schemas.organizations.Create,
    uow: dependencies.uow.Postgres,
    org_service: dependencies.services.Organizations,
    memberships_service: dependencies.services.Memberships,
    current_user: dependencies.permissions.ActiveUser,
):
    org = await org_service.create(uow, organization_create)
    await memberships_service.create(
        uow,
        schemas.memberships.Create(
            organization_id=org.id,
            user_id=current_user.id,
            role=models.UserRoles.OWNER,
            status=models.MembershipStatuses.APPROVED,
        ),
    )
    return org


@router.get(
    "",
    response_model=list[schemas.organizations.Read],
)
async def read_organizations(
    uow: dependencies.uow.Postgres,
    service: dependencies.services.Organizations,
    filters: FiltersQuery,
    sorting: SortingQuery,
    pagination: dependencies.queries.Pagination,
    optional_user: dependencies.permissions.OptionalUser,
):
    return await service.read_many(
        uow,
        filters,
        sorting,
        pagination,
        include_deleted=optional_user.is_admin if optional_user else False,
    )


@router.get(
    "/{organization_id}",
    response_model=schemas.organizations.Read,
)
async def read_organization(
    organization_id: UUID,
    uow: dependencies.uow.Postgres,
    service: dependencies.services.Organizations,
    optional_user: dependencies.permissions.OptionalUser,
):
    return await service.read_by_id(
        uow, organization_id, include_deleted=optional_user.is_admin if optional_user else False
    )


@router.patch(
    "/{organization_id}",
    response_model=schemas.organizations.Read,
    dependencies=[Depends(dependencies.permissions.get_org_editor)],
)
async def update_organization(
    organization_id: UUID,
    organization_update: schemas.organizations.Update,
    uow: dependencies.uow.Postgres,
    service: dependencies.services.Organizations,
):
    return await service.update_by_id(uow, organization_id, organization_update)


@router.delete(
    "/{organization_id}", dependencies=[Depends(dependencies.permissions.get_org_owner)]
)
async def delete_organization(
    organization_id: UUID,
    uow: dependencies.uow.Postgres,
    service: dependencies.services.Organizations,
):
    return {"is_success": await service.delete_by_id(uow, organization_id)}


@router.post(
    "/{organization_id}/image",
    response_model=schemas.organizations.Read,
    dependencies=[Depends(dependencies.permissions.get_org_editor)],
)
async def upload_organization_image(
    organization_id: UUID,
    uow: dependencies.uow.Postgres,
    service: dependencies.services.Organizations,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="Organization image")],
):
    if not file.content_type or file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only image files are allowed. Valid types: "
            f"{', '.join(settings.ALLOWED_IMAGE_TYPES)}",
        )

    return await service.upload_image(uow, organization_id, file, background_tasks)


@router.delete(
    "/{organization_id}/image",
    response_model=schemas.organizations.Read,
    dependencies=[Depends(dependencies.permissions.get_org_editor)],
)
async def delete_organization_image(
    organization_id: UUID,
    uow: dependencies.uow.Postgres,
    service: dependencies.services.Organizations,
    background_tasks: BackgroundTasks,
):
    return await service.delete_image(uow, organization_id, background_tasks)
