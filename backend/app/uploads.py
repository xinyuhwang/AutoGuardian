"""Checking and preparing uploaded files. Types are detected from file contents, never trusted
from the filename or the browser's Content-Type."""

import hashlib
import io
from dataclasses import dataclass

import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

ACCEPTED_DESCRIPTION = "PDF, JPEG, PNG or HEIC"
_HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1"}


class UnsupportedFile(ValueError):
    pass


def sniff_type(data: bytes) -> str | None:
    """Return the real MIME type from the first bytes, or None if unsupported."""
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12] in _HEIC_BRANDS:
        return "image/heic"
    return None


@dataclass
class PreparedFile:
    data: bytes  # what the app reads later (PDF/JPEG/PNG)
    content_type: str
    extension: str
    sha256: str
    original: bytes | None = None  # set only when converted (HEIC)
    original_content_type: str | None = None


_EXTENSIONS = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}


def heic_to_jpeg(data: bytes) -> bytes:
    with Image.open(io.BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image)  # keep the photo the right way up
        out = io.BytesIO()
        image.convert("RGB").save(out, format="JPEG", quality=90)
        return out.getvalue()


def prepare(data: bytes) -> PreparedFile:
    if not data:
        raise UnsupportedFile("The file is empty.")
    content_type = sniff_type(data)
    if content_type is None:
        raise UnsupportedFile(f"Unsupported file type. Upload a {ACCEPTED_DESCRIPTION}.")

    original = original_type = None
    if content_type == "image/heic":
        try:
            original, original_type = data, content_type
            data, content_type = heic_to_jpeg(data), "image/jpeg"
        except Exception as exc:  # corrupt or unusual HEIC
            raise UnsupportedFile("This HEIC photo couldn't be read. Try exporting it as JPEG.") from exc

    return PreparedFile(
        data=data,
        content_type=content_type,
        extension=_EXTENSIONS[content_type],
        sha256=hashlib.sha256(data).hexdigest(),
        original=original,
        original_content_type=original_type,
    )
