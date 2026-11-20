"""File storage for uploaded documents.

Local disk for now. Everything else only uses `save` / `path_for` with opaque keys, so this can
be swapped for S3-compatible storage later without touching the rest of the app.
"""

import uuid
from pathlib import Path

from app.config import UPLOAD_DIR


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def save(self, data: bytes, prefix: str, extension: str) -> str:
        """Write bytes under a new random name; return the storage key (a relative path)."""
        key = f"{prefix}/{uuid.uuid4().hex}{extension}"
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):  # never allow "../" escapes
            raise ValueError("Invalid storage key")
        return path


def get_storage() -> LocalStorage:
    """FastAPI dependency (tests override it with a temporary folder)."""
    return LocalStorage(UPLOAD_DIR)
