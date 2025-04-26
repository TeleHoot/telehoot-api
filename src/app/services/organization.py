import uuid
from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID

from fastapi import BackgroundTasks, UploadFile

from src import core
from src.app import models, repositories, schemas
from src.core.uow import UnitOfWork
from src.core.utils.decorators import log_operation


class Organizations(
    core.services.BaseCRUD[
        schemas.organizations.Create,
        schemas.organizations.Read,
        schemas.organizations.Update,
        models.Organization,
    ]
):
    def __init__(self):
        self.s3 = core.repositories.s3.Base()
        super().__init__(
            repositories.Organizations(),
            create_schema=schemas.organizations.Create,
            read_schema=schemas.organizations.Read,
            update_schema=schemas.organizations.Update,
        )

    async def upload_image(
        self,
        uow: core.uow.UnitOfWork,
        organization_id: UUID,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> schemas.organizations.Read:
        organization = await self.read_by_id(uow, organization_id)

        s3_path = f"{datetime.now(tz=UTC).strftime("%Y/%m/%d")}/{uuid.uuid4()}"

        file_content = await file.read()

        background_tasks.add_task(
            self._process_image_upload,
            file_content=file_content,
            s3_path=s3_path,
            content_type=file.content_type if file.content_type else "image/jpeg",
            old_image_path=organization.image_path,
        )

        return await self.update_by_id(uow, organization_id, {"image_path": s3_path})

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
        uow: core.uow.UnitOfWork,
        organization_id: UUID,
        background_tasks: BackgroundTasks,
    ) -> schemas.organizations.Read:
        organization = await self.read_by_id(uow, organization_id)

        if not organization.image_path:
            return organization

        background_tasks.add_task(self._delete_file_in_background, organization.image_path)

        return await self.update_by_id(uow, organization_id, {"image_path": None})

    async def _delete_file_in_background(self, s3_path: str):
        async with self.s3:
            await self.s3.delete_file(s3_path)
