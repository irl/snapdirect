from google.cloud import storage

from src.google.config import settings


def upload_blob(file_name: str, content: bytes, content_type: str) -> None:
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.BUCKET_NAME)
    blob = bucket.blob(file_name)
    blob.upload_from_string(content, content_type=content_type)
