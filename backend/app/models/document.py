from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.vehicle import Vehicle


class Document(TimestampMixin, Base):
    """One uploaded paper from a shop visit (invoice, inspection report, ...).
    May consist of several files, e.g. three photos of a three-page report."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    # Set by AI extraction in step 1.6: invoice / inspection / battery_test / estimate / obd_report / other.
    kind: Mapped[str | None] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(String(500))  # optional user note
    # pending → (step 1.6) extracting → extracted / failed → (step 1.7) committed
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")

    vehicle: Mapped["Vehicle"] = relationship()
    files: Mapped[list["DocumentFile"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentFile.position",
    )


class DocumentFile(TimestampMixin, Base):
    """One file (page/photo) of a document. Originals are kept forever."""

    __tablename__ = "document_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]  # page order, starting at 0
    original_filename: Mapped[str] = mapped_column(String(255))

    # The file the app reads (PDF, JPEG or PNG). For HEIC uploads this is the converted JPEG.
    storage_key: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64))

    # Only set when the upload was converted (HEIC → JPEG): the untouched original.
    original_storage_key: Mapped[str | None] = mapped_column(String(500))
    original_content_type: Mapped[str | None] = mapped_column(String(100))

    document: Mapped["Document"] = relationship(back_populates="files")
