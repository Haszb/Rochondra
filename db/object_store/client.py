from minio import Minio

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "rochondra"
MINIO_SECRET_KEY = "devpassword123"

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,  # True en prod avec HTTPS
)


def ensure_bucket(bucket_name: str) -> None:
    """Create the bucket if it doesn't already exist."""
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)