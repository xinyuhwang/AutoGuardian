"""Document upload, listing and file download. Everything is scoped to the logged-in user's
own vehicles; anything else returns 404."""

from datetime import datetime
from pathlib import PurePath
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app import uploads
from app.auth.deps import CurrentUser, DbSession
from app.config import MAX_FILES_PER_DOCUMENT, MAX_UPLOAD_BYTES
from app.models import Document, DocumentFile, Vehicle
from app.routers.vehicles import get_owned_vehicle
from app.storage import LocalStorage, get_storage

router = APIRouter(tags=["documents"])

Storage = Annotated[LocalStorage, Depends(get_storage)]


class DocumentFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    original_filename: str
    content_type: str
    size_bytes: int
    converted_from: str | None = None  # e.g. "image/heic"


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    kind: str | None
    note: str | None
    extraction_status: str
    created_at: datetime
    files: list[DocumentFileOut]


def _to_out(document: Document) -> DocumentOut:
    out = DocumentOut.model_validate(document)
    for file_out, file in zip(out.files, document.files):
        file_out.converted_from = file.original_content_type
    return out


def _read_limited(upload: UploadFile) -> bytes:
    data = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"“{upload.filename}” is larger than {limit_mb} MB.",
        )
    return data


@router.post("/vehicles/{vehicle_id}/documents", status_code=status.HTTP_201_CREATED)
def upload_document(
    vehicle_id: int,
    db: DbSession,
    user: CurrentUser,
    storage: Storage,
    files: Annotated[list[UploadFile], File(description="One or more pages: PDF, JPEG, PNG or HEIC")],
    note: Annotated[str | None, Form(max_length=500)] = None,
) -> DocumentOut:
    vehicle = get_owned_vehicle(db, user, vehicle_id)
    if not files:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Choose at least one file.")
    if len(files) > MAX_FILES_PER_DOCUMENT:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"A document can have at most {MAX_FILES_PER_DOCUMENT} files.",
        )

    # Validate and convert everything first, so a bad file doesn't leave a half-saved document.
    prepared: list[tuple[UploadFile, uploads.PreparedFile]] = []
    for upload in files:
        try:
            prepared.append((upload, uploads.prepare(_read_limited(upload))))
        except uploads.UnsupportedFile as exc:
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"“{upload.filename}”: {exc}"
            )

    document = Document(vehicle_id=vehicle.id, note=(note or "").strip() or None)
    db.add(document)
    db.flush()  # assigns document.id for the storage folder

    prefix = f"vehicles/{vehicle.id}/documents/{document.id}"
    for position, (upload, p) in enumerate(prepared):
        original_key = (
            storage.save(p.original, prefix, ".heic") if p.original is not None else None
        )
        document.files.append(
            DocumentFile(
                position=position,
                original_filename=(upload.filename or f"file-{position + 1}")[:255],
                storage_key=storage.save(p.data, prefix, p.extension),
                content_type=p.content_type,
                size_bytes=len(p.data),
                sha256=p.sha256,
                original_storage_key=original_key,
                original_content_type=p.original_content_type,
            )
        )
    db.commit()
    db.refresh(document)
    return _to_out(document)


@router.get("/vehicles/{vehicle_id}/documents")
def list_documents(vehicle_id: int, db: DbSession, user: CurrentUser) -> list[DocumentOut]:
    vehicle = get_owned_vehicle(db, user, vehicle_id)
    documents = db.scalars(
        select(Document)
        .where(Document.vehicle_id == vehicle.id)
        .order_by(Document.created_at.desc(), Document.id.desc())
    ).all()
    return [_to_out(d) for d in documents]


@router.get("/documents/{document_id}/files/{file_id}")
def download_file(
    document_id: int,
    file_id: int,
    db: DbSession,
    user: CurrentUser,
    storage: Storage,
    original: bool = False,
) -> FileResponse:
    """Stream a stored file (inline, for viewing). `original=true` returns the HEIC original."""
    file = db.scalars(
        select(DocumentFile)
        .join(Document)
        .join(Vehicle)
        .where(
            DocumentFile.id == file_id,
            DocumentFile.document_id == document_id,
            Vehicle.user_id == user.id,
        )
    ).first()
    if file is None or (original and file.original_storage_key is None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")

    key = file.original_storage_key if original else file.storage_key
    media_type = file.original_content_type if original else file.content_type
    path = storage.path_for(key)
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File is missing from storage")
    filename = file.original_filename
    if not original and file.original_content_type:  # converted: name it by what it now is
        filename = f"{PurePath(filename).stem}.jpg"
    return FileResponse(
        path,
        media_type=media_type,
        filename=filename,
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"},
    )
