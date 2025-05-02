from io import BytesIO

from beanie import PydanticObjectId
from fastapi import BackgroundTasks, UploadFile

from src import core
from src.app import models, repositories, schemas


class Questions(
    core.services.BaseCRUD[
        schemas.questions.Create,
        schemas.questions.Read,
        schemas.questions.Update,
        schemas.questions.Filters,
        schemas.questions.SortParams,
        models.Question,
    ]
):
    def __init__(self):
        self.s3 = core.repositories.s3.Base()
        self.repo = repositories.Questions()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.questions.Create,
            read_schema=schemas.questions.Read,
            update_schema=schemas.questions.Update,
            filters_schema=schemas.questions.Filters,
        )

    async def upload_question_media(
        self,
        uow: core.UnitOfWork,
        question_id: PydanticObjectId,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> schemas.questions.Read:
        question = await self.read_by_id(uow, question_id)

        s3_path = await self.s3.generate_upload_path()

        file_content = await file.read()

        background_tasks.add_task(
            self._process_media_upload,
            file_content=file_content,
            s3_path=s3_path,
            content_type=file.content_type or "application/octet-stream",
            old_media_path=question.media_path,
        )

        return await self.update_by_id(
            uow, question_id, schemas.questions.Update(media_path=s3_path)
        )

    async def _process_media_upload(
        self,
        file_content: bytes,
        s3_path: str,
        content_type: str,
        old_media_path: str | None = None,
    ):
        async with self.s3:
            try:
                await self.s3.upload_fileobj(
                    fileobj=BytesIO(file_content), s3_path=s3_path, content_type=content_type
                )

                if old_media_path:
                    await self.s3.delete_file(old_media_path)
            except Exception:
                self.logger.exception("Failed to process media upload")

    async def delete_question_media(
        self,
        uow: core.UnitOfWork,
        question_id: PydanticObjectId,
        background_tasks: BackgroundTasks,
    ) -> schemas.questions.Read:
        question = await self.read_by_id(uow, question_id)

        if not question.media_path:
            return question

        background_tasks.add_task(self._delete_file_in_background, question.media_path)

        return await self.update_by_id(uow, question_id, schemas.questions.Update(media_path=None))

    async def _delete_file_in_background(self, s3_path: str) -> None:
        async with self.s3:
            await self.s3.delete_file(s3_path)

    async def read_by_id(
        self, uow: core.UnitOfWork, question_id: PydanticObjectId
    ) -> schemas.questions.Read:
        question = await super().read_by_id(uow, question_id)
        return await self._inject_media_url(question)

    async def read_many(
        self,
        uow: core.UnitOfWork,
        filters: schemas.questions.Filters | None = None,
        sorting: schemas.questions.SortParams | None = None,
        pagination: core.schemas.PaginationParams | None = None,
    ) -> list[schemas.questions.Read]:
        questions = await super().read_many(uow, filters, sorting, pagination)
        return [await self._inject_media_url(question) for question in questions]

    async def update_by_id(
        self,
        uow: core.UnitOfWork,
        question_id: PydanticObjectId,
        update_schema: schemas.questions.Update,
    ) -> schemas.questions.Read:
        question = await super().update_by_id(uow, question_id, update_schema)
        return await self._inject_media_url(question)

    async def _inject_media_url(self, question: schemas.questions.Read) -> schemas.questions.Read:
        media_url = (
            await self._get_media_url(str(question.id), question.media_path)
            if question.media_path
            else None
        )
        question.media_path = media_url
        return question

    async def _get_media_url(self, question_id: str, media_path: str) -> str | None:
        try:
            async with self.s3:
                return await self.s3.generate_download_url(
                    media_path, f"question_{question_id}_media", expiration_minutes=5
                )
        except Exception as e:  # noqa: BLE001
            self.logger.warning("Failed to generate media URL: %s", e)
            return None
