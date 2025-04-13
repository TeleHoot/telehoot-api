from fastapi import APIRouter
from fastapi.params import Query
from uuid import UUID

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
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    return await service.read_all(session, page=page, limit=limit)


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