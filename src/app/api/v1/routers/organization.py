from uuid import UUID

from fastapi import APIRouter

from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/organization", tags=["organization"])


@router.post("/", response_model=schemas.OrganizationRead)
async def create_organization(
    organization_create: schemas.OrganizationCreate,
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
):
    return await service.create(session, organization_create)


@router.post("/bulk/", response_model=list[schemas.OrganizationRead])
async def create_organizations(
    organizations_create: list[schemas.OrganizationCreate],
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
):
    return await service.create_many(session, organizations_create)


@router.get("/{organization_id}", response_model=schemas.OrganizationRead)
async def read_organization(
    organization_id: UUID,
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
):
    return await service.read_by_id(session, organization_id)


@router.get("/", response_model=list[schemas.OrganizationRead])
async def read_organizations(
    session: dependencies.DBSession,
    service: dependencies.OrganizationService,
    filter_query: dependencies.PageLimitQuery,
):
    return await service.read_many(session, page=filter_query.page, limit=filter_query.limit)


@router.patch("/{organization_id}", response_model=schemas.OrganizationRead)
async def update_organization(
    organization_id: UUID,
    organization_update: schemas.OrganizationUpdate,
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
