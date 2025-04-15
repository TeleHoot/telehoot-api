from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/organizations", tags=["organizations"])
settings = core.config.get_settings()


@router.post("/", response_model=schemas.organizations.Read)
async def create_organization(
    organization_create: schemas.organizations.Create,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
):
    return await service.create(uow, organization_create)


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


@router.patch("/{organization_id}", response_model=schemas.organizations.Read)
async def update_organization(
    organization_id: UUID,
    organization_update: schemas.organizations.Update,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
):
    return await service.update_by_id(uow, organization_id, organization_update)


@router.delete("/{organization_id}", response_model=bool)
async def delete_organization(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
):
    return await service.delete_by_id(uow, organization_id)


@router.post("/{organization_id}/image", response_model=schemas.organizations.Read)
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


@router.delete("/{organization_id}/image", response_model=schemas.organizations.Read)
async def delete_organization_image(
    organization_id: UUID,
    uow: dependencies.PostgresUOW,
    service: dependencies.OrganizationService,
    background_tasks: BackgroundTasks,
):
    return await service.delete_image(uow, organization_id, background_tasks)
