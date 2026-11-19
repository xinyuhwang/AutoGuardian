from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        # A user can't register the same VIN twice; different users may (e.g. after a sale).
        UniqueConstraint("user_id", "vin", name="uq_vehicles_user_id_vin"),
        CheckConstraint("length(vin) = 17", name="vin_length"),
        CheckConstraint("purchase_mileage >= 0", name="purchase_mileage_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Identity: VIN is optional so a car can be added before the VIN is at hand.
    vin: Mapped[str | None] = mapped_column(String(17))
    year: Mapped[int]
    make: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    trim: Mapped[str | None] = mapped_column(String(50))
    engine: Mapped[str | None] = mapped_column(String(100))
    transmission: Mapped[str | None] = mapped_column(String(100))

    # Ownership context used by the alert engine later.
    nickname: Mapped[str | None] = mapped_column(String(50))
    purchase_date: Mapped[date | None] = mapped_column(Date)
    purchase_mileage: Mapped[int | None]
    home_zip: Mapped[str | None] = mapped_column(String(10))  # climate-aware alerts

    owner: Mapped["User"] = relationship(back_populates="vehicles")
