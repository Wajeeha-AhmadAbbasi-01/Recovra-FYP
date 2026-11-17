import hashlib
import uuid
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


def ensure_storage_dir() -> Path:
    root = Path(settings.upload_storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def store_bytes(data: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(data).hexdigest()
    key = f"{uuid.uuid4().hex}.pdf"
    path = ensure_storage_dir() / key
    path.write_bytes(data)
    return key, digest


def resolve_path(storage_key: str) -> Path:
    path = ensure_storage_dir() / storage_key
    if not path.exists():
        raise FileNotFoundError(storage_key)
    return path