from uuid import UUID

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src import core
from src.app import models, repositories, schemas


class Organizations(
    core.services.BaseCRUD[
        schemas.OrganizationCreate,
        schemas.OrganizationRead,
        schemas.OrganizationUpdate,
        models.Organization,
    ]
):
    def __init__(self):
        self.repo = repositories.Organizations()
        self.s3 = core.repositories.S3()
        super().__init__(
            self.repo,
            create_schema=schemas.OrganizationCreate,
            read_schema=schemas.OrganizationRead,
            update_schema=schemas.OrganizationUpdate,
        )

    async def upload_image(
        self,
        session: AsyncSession,
        organization_id: UUID,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> schemas.OrganizationRead:
        organization = await self.repo.read_by_id(session, organization_id)

        s3_path = self.s3.generate_upload_path_with_file_name()
        self.s3.upload_fileobj(file.file, s3_path, file.content_type)

        if organization.image_path:
            background_tasks.add_task(self.s3.delete_file, organization.image_path)

        updated_org = await self.repo.update_by_id(
            session, organization_id, {"image_path": s3_path}
        )

        return self._validate_data(updated_org)

    async def delete_image(
        self,
        session: AsyncSession,
        organization_id: UUID,
        background_tasks: BackgroundTasks,
    ) -> schemas.OrganizationRead:
        organization = await self.read_by_id(session, organization_id)

        if not organization.image_path:
            return self._validate_data(organization)

        background_tasks.add_task(self.s3.delete_file, organization.image_path)

        updated_org = await self.repo.update_by_id(session, organization_id, {"image_path": None})

        return self._validate_data(updated_org)

    def _validate_data(self, entity: models.Organization) -> schemas.OrganizationRead:
        data = entity.__dict__

        if hasattr(entity, "image_path") and entity.image_path:
            data["image_url"] = self._get_image_url(str(entity.id), entity.image_path)
        else:
            data["image_url"] = None

        return self.read_schema.model_validate(data)

    def _get_image_url(self, org_id: str, image_path: str) -> str | None:
        try:
            return self.s3.generate_download_url(
                image_path, f"organization_{org_id}_image.jpg", expiration_minutes=5
            )
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"Failed to generate image URL: {e}")  # noqa: G004
            return None
