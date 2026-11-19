"""Vehicle endpoints. Every query is filtered by the logged-in user, so one user can never
read or change another user's vehicles. (VIN decoding arrives in step 1.4.)"""

from datetime import date

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.deps import CurrentUser, DbSession
from app.models import Vehicle

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


class VehicleIn(BaseModel):
    vin: str | None = Field(default=None, min_length=17, max_length=17)
    year: int = Field(ge=1981, le=2100)  # 17-character VINs began in 1981
    make: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    trim: str | None = Field(default=None, max_length=50)
    engine: str | None = Field(default=None, max_length=100)
    transmission: str | None = Field(default=None, max_length=100)
    nickname: str | None = Field(default=None, max_length=50)
    purchase_date: date | None = None
    purchase_mileage: int | None = Field(default=None, ge=0)
    home_zip: str | None = Field(default=None, max_length=10)


class VehicleOut(VehicleIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


def _get_owned_vehicle(db: DbSession, user: CurrentUser, vehicle_id: int) -> Vehicle:
    vehicle = db.scalars(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.user_id == user.id)
    ).first()
    if vehicle is None:
        # 404 (not 403) so other users' vehicle IDs aren't revealed.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    return vehicle


@router.get("")
def list_vehicles(db: DbSession, user: CurrentUser) -> list[VehicleOut]:
    vehicles = db.scalars(
        select(Vehicle).where(Vehicle.user_id == user.id).order_by(Vehicle.id)
    ).all()
    return [VehicleOut.model_validate(v) for v in vehicles]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_vehicle(body: VehicleIn, db: DbSession, user: CurrentUser) -> VehicleOut:
    data = body.model_dump()
    if data["vin"]:
        data["vin"] = data["vin"].upper()
    vehicle = Vehicle(user_id=user.id, **data)
    db.add(vehicle)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "You already added a vehicle with this VIN")
    return VehicleOut.model_validate(vehicle)


@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: int, db: DbSession, user: CurrentUser) -> VehicleOut:
    return VehicleOut.model_validate(_get_owned_vehicle(db, user, vehicle_id))
