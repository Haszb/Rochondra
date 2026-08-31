from minio import Minio

from core_shared.config import MinioConfig

client = Minio(
    MinioConfig.ENDPOINT,
    access_key=MinioConfig.ACCESS_KEY,
    secret_key=MinioConfig.SECRET_KEY,
    secure=MinioConfig.SECURE,
)


def ensure_bucket(bucket_name: str) -> None:
    """Create the bucket if it doesn't already exist."""
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
