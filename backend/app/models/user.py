from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.vehicle import Vehicle


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Always stored lowercase (see app.auth.service.normalize_email).
    email: Mapped[str] = mapped_column(String(320), unique=True)
    # Argon2 hash; the plain password is never stored.
    password_hash: Mapped[str] = mapped_column(String(255))

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
