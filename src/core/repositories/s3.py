import logging
import uuid
from datetime import UTC, datetime
from typing import BinaryIO

import aioboto3
from botocore.exceptions import ClientError

from src.core.config import get_settings
from src.core.utils.decorators import log_operation

settings = get_settings()


class Base:
    """
    Async S3 repository using aioboto3 with connection pooling.
    """

    def __init__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=settings.S3.ACCESS_KEY,
            aws_secret_access_key=settings.S3.SECRET_KEY,
            region_name=settings.S3.REGION,
        )
        self._client = None
        self._endpoint_url = (
            settings.S3.INTERNAL_URL if settings.S3.IS_PROXY_REQUIRED else settings.S3.ENDPOINT
        )
        self._use_ssl = settings.S3.REQUIRE_TLS
        self._client_error = "S3 client not initialized. Use async context manager"
        self.logger = logging.getLogger(f"repositories.{__name__.lower()}")
        self.context = {
            "bucket": settings.S3.BUCKET_NAME,
        }

    async def __aenter__(self):
        self._client = await self.session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
        ).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None

    @staticmethod
    async def _generate_upload_path() -> str:
        current_yyyy_mm_dd: str = datetime.now(tz=UTC).strftime("%Y/%m/%d")
        return f"{current_yyyy_mm_dd}/"

    async def generate_upload_path_with_file_name(self) -> str:
        return f"{await self._generate_upload_path()}{uuid.uuid4()}"

    @log_operation
    async def upload_fileobj(
        self,
        fileobj: BinaryIO | bytes | bytearray,
        s3_path: str,
        content_type: str | None = None,
    ) -> None:
        if not self._client:
            raise RuntimeError(self._client_error)

        await self._client.upload_fileobj(
            Fileobj=fileobj,
            Bucket=settings.S3.BUCKET_NAME,
            Key=s3_path,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

    @log_operation
    async def delete_file(self, s3_path: str) -> bool:
        if not self._client:
            raise RuntimeError(self._client_error)

        try:
            await self._client.delete_object(
                Bucket=settings.S3.BUCKET_NAME,
                Key=s3_path,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchKey":
                self.logger.warning("Delete target not found", extra={"deleted": False})
        return False

    @log_operation
    async def generate_download_url(
        self,
        s3_path: str,
        desired_filename: str | None = None,
        expiration_minutes: int = 360,
    ) -> str:
        if not self._client:
            raise RuntimeError(self._client_error)

        response_content_disposition = (
            f"attachment; filename={desired_filename or s3_path.split('/')[-1]}"
        )
        params = {
            "Bucket": settings.S3.BUCKET_NAME,
            "Key": s3_path,
            "ResponseContentDisposition": response_content_disposition,
        }

        return await self._client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expiration_minutes * 60,
        )
