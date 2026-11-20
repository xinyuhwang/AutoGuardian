"""Vehicle endpoints. Every query is filtered by the logged-in user, so one user can never
read or change another user's vehicles."""

from collections.abc import Iterator
from dataclasses import asdict
from datetime import date
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import vin as vin_service
from app.auth.deps import CurrentUser, DbSession
from app.models import Vehicle

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def get_http_client() -> Iterator[httpx.Client]:
    """Outbound HTTP client (overridden in tests so they never hit the network)."""
    with httpx.Client(headers={"User-Agent": "AutoGuardian"}) as client:
        yield client


HttpClient = Annotated[httpx.Client, Depends(get_http_client)]


class VinDecodeOut(BaseModel):
    """Proposed vehicle details from NHTSA. Nothing is saved until the user confirms."""

    vin: str
    year: int | None
    make: str | None
    model: str | None
    trim: str | None
    engine: str | None
    transmission: str | None
    body_class: str | None
    drive_type: str | None
    fuel_type: str | None
    warnings: list[str]
    source: str = "NHTSA vPIC"


@router.get("/decode-vin")
def decode_vin(
    vin: Annotated[str, Query(max_length=40)], user: CurrentUser, client: HttpClient
) -> VinDecodeOut:
    try:
        normalized = vin_service.normalize_vin(vin)
    except vin_service.InvalidVin as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))
    try:
        decoded = vin_service.decode_vin(normalized, client)
    except vin_service.VinLookupUnavailable:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "The NHTSA VIN lookup is unavailable right now. You can enter the details manually.",
        )
    return VinDecodeOut(**asdict(decoded))


class VehicleIn(BaseModel):
    vin: str | None = Field(default=None, max_length=40)  # normalized to 17 chars on save
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
    data["vin"] = data["vin"] or None  # treat "" as "no VIN"
    if data["vin"]:
        try:
            data["vin"] = vin_service.normalize_vin(data["vin"])
        except vin_service.InvalidVin as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))
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
