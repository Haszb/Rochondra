import io
import json
from pathlib import Path

from minio.commonconfig import CopySource
from minio.error import S3Error

from core_shared.config import MinioConfig
from db.object_store.client import client, ensure_bucket

TEMP_BUCKET = MinioConfig.TEMP_BUCKET
DOCUMENTS_BUCKET = MinioConfig.DOCUMENTS_BUCKET


def upload_pdf_to_temp(uuid: str, pdf_path: Path | str) -> None:
    """Upload the raw PDF to the temporary staging bucket."""
    ensure_bucket(TEMP_BUCKET)
    client.fput_object(TEMP_BUCKET, f"pdf/{uuid}.pdf", str(pdf_path))


def upload_markdown_to_temp(uuid: str, md_path: Path | str) -> None:
    """Upload the extracted markdown to the temporary staging bucket."""
    ensure_bucket(TEMP_BUCKET)
    client.fput_object(TEMP_BUCKET, f"markdown/{uuid}.md", str(md_path))


def upload_images_to_temp(uuid: str, img_dir: Path | str) -> int:
    """Upload every image found in *img_dir* to the temporary staging bucket.

    Returns:
        The number of images uploaded (0 if the directory doesn't exist or is empty).
    """
    ensure_bucket(TEMP_BUCKET)
    img_dir_path = Path(img_dir)
    if not img_dir_path.exists():
        return 0

    count = 0
    for img_file in img_dir_path.iterdir():
        if img_file.is_file():
            client.fput_object(TEMP_BUCKET, f"images/{uuid}/{img_file.name}", str(img_file))
            count += 1
    return count

def download_pdf_from_temp(uuid: str, dest_path: Path | str) -> None:
    """Download the raw PDF from the temporary staging bucket to *dest_path*."""
    client.fget_object(TEMP_BUCKET, f"pdf/{uuid}.pdf", str(dest_path))

def download_markdown_from_temp(uuid: str, dest_path: Path | str) -> None:
    """Download the markdown file from the temporary staging bucket to *dest_path*."""
    client.fget_object(TEMP_BUCKET, f"markdown/{uuid}.md", str(dest_path))

def download_images_from_temp(uuid: str, dest_dir: Path | str) -> int:
    """Download every image for *uuid* from the temporary staging bucket into *dest_dir*.

    Returns:
        The number of images downloaded (0 if none exist for this uuid).
    """
    dest_dir_path = Path(dest_dir)
    dest_dir_path.mkdir(parents=True, exist_ok=True)

    count = 0
    objects = client.list_objects(TEMP_BUCKET, prefix=f"images/{uuid}/", recursive=True)
    for obj in objects:
        if obj.object_name is None:
            continue  

        filename = Path(obj.object_name).name
        client.fget_object(TEMP_BUCKET, obj.object_name, str(dest_dir_path / filename))
        count += 1
    return count

def pdf_exists_in_temp(uuid: str) -> bool:
    """Return ``True`` if the PDF for *uuid* exists in the temporary staging bucket."""
    try:
        client.stat_object(TEMP_BUCKET, f"pdf/{uuid}.pdf")
        return True
    except S3Error:
        return False


def list_pdf_uuids_in_temp() -> list[str]:
    """List every UUID for which a staged PDF exists in the temporary bucket."""
    try:
        ensure_bucket(TEMP_BUCKET)
    except S3Error:
        return []

    uuids: list[str] = []
    for obj in client.list_objects(TEMP_BUCKET, prefix="pdf/", recursive=True):
        if obj.object_name is None:
            continue
        name = Path(obj.object_name).name
        if name.endswith(".pdf"):
            uuids.append(name[:-4])
    return uuids


def upload_json_to_temp(uuid: str, kind: str, payload) -> None:
    """Upload a JSON payload to the temporary staging bucket.

    Args:
        uuid: Document UUID.
        kind: Sub-path under the bucket, e.g. ``"toc"`` or ``"analysis"``.
        payload: Any JSON-serialisable object.
    """
    ensure_bucket(TEMP_BUCKET)
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(TEMP_BUCKET, f"{kind}/{uuid}.json", io.BytesIO(data), length=len(data))


def get_json_from_temp(uuid: str, kind: str):
    """Fetch and parse a JSON payload from the temporary staging bucket.

    Raises:
        minio.error.S3Error: If the object does not exist.
    """
    response = client.get_object(TEMP_BUCKET, f"{kind}/{uuid}.json")
    try:
        return json.loads(response.read())
    finally:
        response.close()
        response.release_conn()


def json_exists_in_temp(uuid: str, kind: str) -> bool:
    """Return ``True`` if the JSON object exists in the temporary staging bucket."""
    try:
        client.stat_object(TEMP_BUCKET, f"{kind}/{uuid}.json")
        return True
    except S3Error:
        return False


def upload_json_to_documents(uuid: str, kind: str, payload) -> None:
    """Upload a JSON payload to the permanent documents bucket."""
    ensure_bucket(DOCUMENTS_BUCKET)
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(DOCUMENTS_BUCKET, f"{kind}/{uuid}.json", io.BytesIO(data), length=len(data))


def _temp_keys_for_uuid(uuid: str) -> list[str]:
    """Return every temp-bucket key owned by *uuid* (fixed slots + image files)."""
    keys = [
        f"pdf/{uuid}.pdf",
        f"markdown/{uuid}.md",
        f"toc/{uuid}.json",
        f"analysis/{uuid}.json",
    ]
    for obj in client.list_objects(TEMP_BUCKET, prefix=f"images/{uuid}/", recursive=True):
        if obj.object_name is not None:
            keys.append(obj.object_name)
    return keys


def move_artifacts_from_temp_to_documents(uuid: str) -> list[str]:
    """Move every artifact belonging to *uuid* from temp-bucket to documents-bucket.

    Copies each object then removes the original (S3 has no atomic move).
    Objects that don't exist are silently skipped, so this is safe to call
    even when a document only went through a subset of the pipeline.

    Returns:
        The list of ``bucket/key`` paths written to documents-bucket.
    """
    ensure_bucket(DOCUMENTS_BUCKET)

    moved: list[str] = []
    for key in _temp_keys_for_uuid(uuid):
        try:
            client.copy_object(
                DOCUMENTS_BUCKET,
                key,
                CopySource(TEMP_BUCKET, key),
            )
        except S3Error as e:
            if e.code == "NoSuchKey":
                continue
            raise
        client.remove_object(TEMP_BUCKET, key)
        moved.append(f"{DOCUMENTS_BUCKET}/{key}")

    return moved


def delete_artifacts_from_temp(uuid: str) -> list[str]:
    """Remove every temp-bucket artifact belonging to *uuid*.

    Missing objects are silently skipped, so this is safe to call even when
    a document only went through a subset of the pipeline.

    Returns:
        The list of ``bucket/key`` paths that were deleted.
    """
    deleted: list[str] = []
    for key in _temp_keys_for_uuid(uuid):
        try:
            client.stat_object(TEMP_BUCKET, key)
        except S3Error as e:
            if e.code == "NoSuchKey":
                continue
            raise
        client.remove_object(TEMP_BUCKET, key)
        deleted.append(f"{TEMP_BUCKET}/{key}")

    return deleted