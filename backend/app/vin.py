"""VIN validation and decoding via NHTSA vPIC (free, no API key).

https://vpic.nhtsa.dot.gov/api/  · endpoint: DecodeVinValues/{vin}?format=json
"""

import re
from dataclasses import dataclass, field

import httpx

VPIC_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}"
VPIC_TIMEOUT_SECONDS = 10.0

# VINs never contain I, O or Q (too easily confused with 1 and 0).
_VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")

# Check-digit transliteration and weights (49 CFR 565).
_VALUES = {
    **{str(d): d for d in range(10)},
    **dict(zip("ABCDEFGH", range(1, 9))),
    **dict(zip("JKLMN", range(1, 6))),
    "P": 7,
    "R": 9,
    **dict(zip("STUVWXYZ", range(2, 10))),
}
_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


class InvalidVin(ValueError):
    pass


class VinLookupUnavailable(RuntimeError):
    pass


def normalize_vin(raw: str) -> str:
    """Uppercase, strip spaces/dashes, and check the format. Raises InvalidVin."""
    vin = re.sub(r"[\s-]", "", raw).upper()
    if len(vin) != 17:
        raise InvalidVin(f"A VIN has 17 characters; this one has {len(vin)}.")
    if not _VIN_PATTERN.match(vin):
        bad = sorted({c for c in vin if c in "IOQ" or not c.isalnum()})
        hint = " (VINs never use I, O or Q; try 1 or 0)" if set(bad) & set("IOQ") else ""
        raise InvalidVin(f"Invalid character(s) {', '.join(bad)}{hint}.")
    return vin


def check_digit_ok(vin: str) -> bool:
    """Position 9 check digit. Required for North American vehicles."""
    total = sum(_VALUES[c] * w for c, w in zip(vin, _WEIGHTS))
    expected = "X" if total % 11 == 10 else str(total % 11)
    return vin[8] == expected


@dataclass
class DecodedVin:
    vin: str
    year: int | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None
    engine: str | None = None
    transmission: str | None = None
    body_class: str | None = None
    drive_type: str | None = None
    fuel_type: str | None = None
    warnings: list[str] = field(default_factory=list)


def _clean(value: object) -> str | None:
    text = str(value or "").strip()
    return None if text in ("", "Not Applicable", "0") else text


def _tidy_case(text: str | None) -> str | None:
    """'HONDA' -> 'Honda', 'TOURING' -> 'Touring'; keeps 'EX-L', 'BMW', 'LX' as they are."""
    if not text:
        return text
    return " ".join(w.capitalize() if w.isalpha() and w.isupper() and len(w) >= 4 else w for w in text.split())


def _engine(r: dict) -> str | None:
    parts = []
    if displacement := _clean(r.get("DisplacementL")):
        parts.append(f"{float(displacement):.1f}L")
    if cylinders := _clean(r.get("EngineCylinders")):
        parts.append(f"{cylinders}-cyl")
    if (_clean(r.get("Turbo")) or "").lower() == "yes":
        parts.append("turbo")
    if electrification := _clean(r.get("ElectrificationLevel")):
        parts.append("hybrid" if "HEV" in electrification and "BEV" not in electrification else electrification)
    text = " ".join(parts)
    if model := _clean(r.get("EngineModel")):
        text = f"{text} ({model})" if text else model
    return text or None


def _transmission(r: dict) -> str | None:
    style = _clean(r.get("TransmissionStyle"))
    speeds = _clean(r.get("TransmissionSpeeds"))
    if style and "CVT" in style:
        return "CVT"
    if style and speeds:
        return f"{style}, {speeds}-speed"
    return style


def parse_vpic(vin: str, payload: dict) -> DecodedVin:
    results = payload.get("Results") or [{}]
    r = results[0]
    year = _clean(r.get("ModelYear"))
    decoded = DecodedVin(
        vin=vin,
        year=int(year) if year and year.isdigit() else None,
        make=_tidy_case(_clean(r.get("Make"))),
        model=_clean(r.get("Model")),
        trim=_tidy_case(_clean(r.get("Trim")) or _clean(r.get("Series"))),
        engine=_engine(r),
        transmission=_transmission(r),
        body_class=_clean(r.get("BodyClass")),
        drive_type=_clean(r.get("DriveType")),
        fuel_type=_clean(r.get("FuelTypePrimary")),
    )
    if not check_digit_ok(vin):
        decoded.warnings.append(
            "The VIN's check digit (9th character) doesn't match. This usually means a typo; "
            "please compare it with the VIN on your dashboard or registration."
        )
    if not (decoded.make and decoded.model and decoded.year):
        decoded.warnings.append(
            "NHTSA couldn't identify this vehicle. Double-check the VIN, or enter the details manually."
        )
    return decoded


def decode_vin(vin: str, client: httpx.Client) -> DecodedVin:
    """Look up an already-normalized VIN. Raises VinLookupUnavailable on network/API failure."""
    try:
        response = client.get(
            VPIC_URL.format(vin=vin), params={"format": "json"}, timeout=VPIC_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise VinLookupUnavailable(str(exc)) from exc
    return parse_vpic(vin, payload)
