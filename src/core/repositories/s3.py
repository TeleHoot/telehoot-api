import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from urllib3 import ProxyManager

from minio import Minio, S3Error
from src.core.config import get_settings
from src.core.repositories.exceptions import S3ObjectDoesntExistError


class S3:
    """
    Repository class that provides a façade for application to access the underlying S3 storage.
    """

    minio_client: Minio
    tmp_path: Path

    def __init__(self):
        self.settings = get_settings()
        self.minio_client = Minio(
            self.settings.S3.ENDPOINT,
            access_key=self.settings.S3.ACCESS_KEY,
            secret_key=self.settings.S3.SECRET_KEY,
            region=self.settings.S3.REGION,
            secure=self.settings.S3.REQUIRE_TLS,
            http_client=ProxyManager(self.settings.S3.INTERNAL_URL)
            if self.settings.S3.IS_PROXY_REQUIRED
            else None,
        )
        self.tmp_path = Path("./tmp")

    @staticmethod
    def __generate_upload_path() -> str:
        current_yyyy_mm_dd: str = datetime.now(tz=UTC).strftime("%Y/%m/%d")
        return f"{current_yyyy_mm_dd}/"

    def generate_upload_path_with_file_name(self) -> str:
        return f"{self.__generate_upload_path()}{uuid.uuid4()}"

    def __validate_object_existence(self, s3_object_path: str) -> None:
        try:
            self.minio_client.stat_object(self.settings.S3.BUCKET_NAME, s3_object_path)
        except S3Error as e:
            if e.code == "NoSuchKey":
                error_msg = (
                    f"The S3 object with path='{s3_object_path}' does not exist in the bucket."
                )
                raise S3ObjectDoesntExistError(error_msg) from e
            raise

    def upload_fileobj(self, fileobj, s3_path: str, content_type: str | None) -> None:
        self.minio_client.put_object(
            bucket_name=self.settings.S3.BUCKET_NAME,
            object_name=s3_path,
            data=fileobj,
            length=-1,
            content_type=content_type,  # type: ignore[valid-type]
            part_size=10 * 1024 * 1024,  # 10MB chunks
        )

    def delete_file(self, s3_path: str) -> None:
        try:
            self.minio_client.remove_object(self.settings.S3.BUCKET_NAME, s3_path)
        except S3Error as e:
            if e.code != "NoSuchKey":
                raise

    def generate_download_url(
        self,
        s3_path: str,
        desired_filename: str | None = None,
        expiration_minutes: int = 360,
    ) -> str:
        filename = desired_filename or s3_path.split("/")[-1]
        headers = {"response-content-disposition": f"attachment; filename={filename}"}

        return self.minio_client.presigned_get_object(
            bucket_name=self.settings.S3.BUCKET_NAME,
            object_name=s3_path,
            expires=timedelta(minutes=expiration_minutes),
            response_headers=headers,  # type: ignore[valid-type]
        )
