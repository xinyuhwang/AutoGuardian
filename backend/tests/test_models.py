import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, Vehicle

ACCORD_VIN = "1HGCV1F3XJA000000"  # 17 characters; not a real vehicle


def make_user(db: Session, email: str = "owner@example.com") -> User:
    user = User(email=email, password_hash="not-a-real-hash")
    db.add(user)
    db.flush()
    return user


def test_create_and_read_vehicle(db: Session) -> None:
    user = make_user(db)
    db.add(
        Vehicle(
            user_id=user.id,
            vin=ACCORD_VIN,
            year=2018,
            make="Honda",
            model="Accord",
            purchase_mileage=0,
        )
    )
    db.commit()

    vehicle = db.scalars(select(Vehicle).where(Vehicle.user_id == user.id)).one()
    assert (vehicle.year, vehicle.make, vehicle.model) == (2018, "Honda", "Accord")
    assert vehicle.trim is None and vehicle.engine is None  # unknown until confirmed
    assert vehicle.created_at is not None
    assert vehicle.owner.email == "owner@example.com"


def test_vehicle_without_vin_is_allowed(db: Session) -> None:
    user = make_user(db)
    db.add(Vehicle(user_id=user.id, year=2018, make="Honda", model="Accord"))
    db.flush()


def test_vin_must_be_17_characters(db: Session) -> None:
    user = make_user(db)
    db.add(Vehicle(user_id=user.id, vin="TOOSHORT", year=2018, make="Honda", model="Accord"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_same_user_cannot_add_same_vin_twice(db: Session) -> None:
    user = make_user(db)
    for _ in range(2):
        db.add(Vehicle(user_id=user.id, vin=ACCORD_VIN, year=2018, make="Honda", model="Accord"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_different_users_may_share_a_vin(db: Session) -> None:
    first, second = make_user(db, "a@example.com"), make_user(db, "b@example.com")
    for user in (first, second):
        db.add(Vehicle(user_id=user.id, vin=ACCORD_VIN, year=2018, make="Honda", model="Accord"))
    db.flush()


def test_email_is_unique(db: Session) -> None:
    make_user(db, "dup@example.com")
    with pytest.raises(IntegrityError):
        make_user(db, "dup@example.com")


def test_deleting_user_deletes_their_vehicles(db: Session) -> None:
    user = make_user(db)
    db.add(Vehicle(user_id=user.id, year=2018, make="Honda", model="Accord"))
    db.flush()
    db.delete(user)
    db.flush()
    assert db.scalars(select(Vehicle)).all() == []
