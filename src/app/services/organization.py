import uuid
from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src import core
from src.app import models, repositories, schemas


class Organizations(
    core.services.BaseCRUD[
        schemas.organizations.Create,
        schemas.organizations.Read,
        schemas.organizations.Update,
        models.Organization,
    ]
):
    def __init__(self):
        self.repo = repositories.Organizations()
        self.s3 = core.repositories.s3.Base()
        super().__init__(
            self.repo,
            create_schema=schemas.organizations.Create,
            read_schema=schemas.organizations.Read,
            update_schema=schemas.organizations.Update,
        )

    async def upload_image(
        self,
        session: AsyncSession,
        organization_id: UUID,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> schemas.organizations.Read:
        organization = await self.repo.read_by_id(session, organization_id)

        s3_path = f"{datetime.now(tz=UTC).strftime('%Y/%m/%d')}/{uuid.uuid4()}"

        file_content = await file.read()

        background_tasks.add_task(
            self._process_image_upload,
            file_content=file_content,
            s3_path=s3_path,
            content_type=file.content_type if file.content_type else "image/jpeg",
            old_image_path=organization.image_path,
        )

        updated_org = await self.repo.update_by_id(
            session, organization_id, {"image_path": s3_path}
        )

        return await self._validate_data(updated_org)

    async def _process_image_upload(
        self,
        file_content: bytes,
        s3_path: str,
        content_type: str,
        old_image_path: str | None = None,
    ):
        async with self.s3:
            try:
                await self.s3.upload_fileobj(
                    fileobj=BytesIO(file_content), s3_path=s3_path, content_type=content_type
                )

                if old_image_path:
                    await self.s3.delete_file(old_image_path)
            except Exception:
                self.logger.exception("Failed to process image upload")

    async def delete_image(
        self,
        session: AsyncSession,
        organization_id: UUID,
        background_tasks: BackgroundTasks,
    ) -> schemas.organizations.Read:
        organization = await self.read_by_id(session, organization_id)

        if not organization.image_path:
            return await self._validate_data(organization)

        background_tasks.add_task(self._delete_file_in_background, organization.image_path)

        updated_org = await self.repo.update_by_id(session, organization_id, {"image_path": None})

        return await self._validate_data(updated_org)

    async def _delete_file_in_background(self, s3_path: str):
        async with self.s3:
            await self.s3.delete_file(s3_path)

    async def _validate_data(self, entity: models.Organization) -> schemas.organizations.Read:
        data = entity.__dict__

        if hasattr(entity, "image_path") and entity.image_path:
            data["image_url"] = await self._get_image_url(str(entity.id), entity.image_path)
        else:
            data["image_url"] = None

        return self.read_schema.model_validate(data)

    async def _get_image_url(self, org_id: str, image_path: str) -> str | None:
        try:
            async with self.s3:
                return await self.s3.generate_download_url(
                    image_path, f"organization_{org_id}_image.jpg", expiration_minutes=5
                )
        except Exception as e:  # noqa: BLE001
            self.logger.warning("Failed to generate image URL: %s", e)
            return None
