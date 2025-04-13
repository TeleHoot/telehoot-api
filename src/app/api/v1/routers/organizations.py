from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/organization", tags=["organization"])


@router.post("/", response_model=schemas.organizations.Read)
async def create_organization(
    organization_create: schemas.organizations.Create,
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
):
    return await service.create(session, organization_create)


@router.get("/{organization_id}", response_model=schemas.organizations.Read)
async def read_organization(
    organization_id: UUID,
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
):
    return await service.read_by_id(session, organization_id)


@router.get("/", response_model=list[schemas.organizations.Read])
async def read_organizations(
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
    filter_query: dependencies.PageLimitQuery,
):
    return await service.read_many(session, page=filter_query.page, limit=filter_query.limit)


@router.patch("/{organization_id}", response_model=schemas.organizations.Read)
async def update_organization(
    organization_id: UUID,
    organization_update: schemas.organizations.Update,
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
):
    return await service.update_by_id(session, organization_id, organization_update)


@router.delete("/{organization_id}", response_model=bool)
async def delete_organization(
    organization_id: UUID,
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
):
    return await service.delete_by_id(session, organization_id)


@router.post("/{organization_id}/image", response_model=schemas.organizations.Read)
async def upload_organization_image(
    organization_id: UUID,
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="Organization image")],
):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only image files are allowed"
        )

    return await service.upload_image(session, organization_id, file, background_tasks)


@router.delete("/{organization_id}/image", response_model=schemas.organizations.Read)
async def delete_organization_image(
    organization_id: UUID,
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
    background_tasks: BackgroundTasks,
):
    return await service.delete_image(session, organization_id, background_tasks)
