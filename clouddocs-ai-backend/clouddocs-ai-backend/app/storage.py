import uuid

from supabase import create_client, Client

from app.config import settings

_client: Client = create_client(settings.supabase_url, settings.supabase_service_key)
_BUCKET = settings.supabase_storage_bucket


def upload_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Uploads a file to Supabase Storage and returns the storage path (key)."""
    key = f"{uuid.uuid4()}-{filename}"
    _client.storage.from_(_BUCKET).upload(
        path=key,
        file=file_bytes,
        file_options={"content-type": content_type},
    )
    return key


def download_file(key: str) -> bytes:
    return _client.storage.from_(_BUCKET).download(key)


def delete_file(key: str) -> None:
    _client.storage.from_(_BUCKET).remove([key])

