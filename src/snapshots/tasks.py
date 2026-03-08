from src.google.client import upload_blob


def upload_snapshot(filename: str, content: str) -> None:
    upload_blob(filename, content.encode("utf-8"), "text/html")
