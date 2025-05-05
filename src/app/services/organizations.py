from io import BytesIO
from uuid import UUID

from fastapi import BackgroundTasks, UploadFile

from src import core
from src.app import models, repositories, schemas


class Organizations(
    core.services.BaseCRUD[
        schemas.organizations.Create,
        schemas.organizations.Read,
        schemas.organizations.Update,
        schemas.organizations.Filters,
        schemas.organizations.SortParams,
        models.Organization,
    ]
):
    def __init__(self):
        self.s3 = core.repositories.s3.Base()
        self.repo = repositories.Organizations()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.organizations.Create,
            read_schema=schemas.organizations.Read,
            update_schema=schemas.organizations.Update,
            filters_schema=schemas.organizations.Filters,
        )

    async def upload_image(
        self,
        uow: core.UnitOfWork,
        organization_id: UUID,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> schemas.organizations.Read:
        organization = await self.read_by_id(uow, organization_id)

        s3_path = await self.s3.generate_upload_path()

        file_content = await file.read()

        background_tasks.add_task(
            self._process_image_upload,
            file_content=file_content,
            s3_path=s3_path,
            content_type=file.content_type or "image/jpeg",
            old_image_path=organization.image_path,
        )

        return await self.update_by_id(
            uow, organization_id, schemas.organizations.Update(image_path=s3_path)
        )

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
        uow: core.UnitOfWork,
        organization_id: UUID,
        background_tasks: BackgroundTasks,
    ) -> schemas.organizations.Read:
        organization = await self.read_by_id(uow, organization_id)

        if not organization.image_path:
            return organization

        background_tasks.add_task(self._delete_file_in_background, organization.image_path)

        return await self.update_by_id(
            uow, organization_id, schemas.organizations.Update(image_path=None)
        )

    async def _delete_file_in_background(self, s3_path: str) -> None:
        async with self.s3:
            await self.s3.delete_file(s3_path)

    async def read_by_id(
        self, uow: core.UnitOfWork, entity_id: UUID, *, include_deleted: bool = False
    ) -> schemas.organizations.Read:
        entity = await super().read_by_id(uow, entity_id, include_deleted=include_deleted)
        return await self._inject_image(entity)

    async def read_many(
        self,
        uow: core.UnitOfWork,
        filters: schemas.organizations.Filters | None = None,
        sorting: schemas.organizations.SortParams | None = None,
        pagination: core.schemas.PaginationParams | None = None,
        *,
        include_deleted: bool = False,
    ) -> list[schemas.organizations.Read]:
        entities = await super().read_many(
            uow, filters, sorting, pagination, include_deleted=include_deleted
        )
        return [await self._inject_image(entity) for entity in entities]

    async def update_by_id(
        self,
        uow: core.UnitOfWork,
        entity_id: UUID,
        update_schema: schemas.organizations.Update,
    ) -> schemas.organizations.Read:
        entity = await super().update_by_id(uow, entity_id, update_schema)
        return await self._inject_image(entity)

    async def _inject_image(
        self, organization: schemas.organizations.Read
    ) -> schemas.organizations.Read:
        image_url = (
            await self._get_image_url(str(organization.id), organization.image_path)
            if organization.image_path
            else None
        )
        organization.image_path = image_url
        return organization

    async def _get_image_url(self, org_id: str, image_path: str) -> str | None:
        try:
            async with self.s3:
                return await self.s3.generate_download_url(
                    image_path, f"organization_{org_id}_image.jpg", expiration_minutes=180
                )
        except Exception as e:  # noqa: BLE001
            self.logger.warning("Failed to generate image URL: %s", e)
            return None
