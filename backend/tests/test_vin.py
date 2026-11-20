import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.vehicles import get_http_client
from app.vin import InvalidVin, check_digit_ok, normalize_vin, parse_vpic

# Sample VINs with valid check digits (not real cars). vPIC fields copied from real responses.
ACCORD_15T_VIN = "1HGCV1F55JA000001"
ACCORD_20T_VIN = "1HGCV2F94JA000001"

ACCORD_15T = {
    "ErrorCode": "0", "ModelYear": "2018", "Make": "HONDA", "Model": "Accord", "Trim": "EX-L",
    "Series": "", "BodyClass": "Sedan/Saloon", "DisplacementL": "1.5", "EngineCylinders": "4",
    "EngineModel": "L15BE", "Turbo": "Yes", "FuelTypePrimary": "Gasoline", "ElectrificationLevel": "",
    "TransmissionStyle": "Continuously Variable Transmission (CVT)", "TransmissionSpeeds": "",
    "DriveType": "4x2",
}
ACCORD_20T = {
    **ACCORD_15T, "Trim": "TOURING", "DisplacementL": "2.0", "EngineModel": "K20C4",
    "TransmissionStyle": "Automatic", "TransmissionSpeeds": "10",
}
UNDECODABLE = {"ErrorCode": "1,7,11,400", "ModelYear": "", "Make": "", "Model": "", "Trim": ""}


def payload(results: dict) -> dict:
    return {"Count": 1, "Results": [results]}


# --- format & check digit -------------------------------------------------------------


def test_normalize_strips_spaces_dashes_and_uppercases() -> None:
    assert normalize_vin(" 1hgcv1f55-ja 000001 ") == ACCORD_15T_VIN


@pytest.mark.parametrize(
    ("raw", "message"),
    [("1HGCV1F55JA00000", "17 characters"), ("1HGCV1F55JA00000O", "never use I, O or Q"), ("1HGCV1F55JA00000!", "Invalid")],
)
def test_normalize_rejects_bad_vins(raw: str, message: str) -> None:
    with pytest.raises(InvalidVin, match=message):
        normalize_vin(raw)


def test_check_digit() -> None:
    assert check_digit_ok(ACCORD_15T_VIN)
    assert check_digit_ok(ACCORD_20T_VIN)
    assert not check_digit_ok("1HGCV1F51JA000001")  # one typo in position 9


# --- parsing vPIC ---------------------------------------------------------------------


def test_parse_accord_15t() -> None:
    d = parse_vpic(ACCORD_15T_VIN, payload(ACCORD_15T))
    assert (d.year, d.make, d.model, d.trim) == (2018, "Honda", "Accord", "EX-L")
    assert d.engine == "1.5L 4-cyl turbo (L15BE)"
    assert d.transmission == "CVT"
    assert d.warnings == []


def test_parse_accord_20t() -> None:
    d = parse_vpic(ACCORD_20T_VIN, payload(ACCORD_20T))
    assert d.trim == "Touring"
    assert d.engine == "2.0L 4-cyl turbo (K20C4)"
    assert d.transmission == "Automatic, 10-speed"


def test_parse_hybrid() -> None:
    hybrid = {**ACCORD_15T, "DisplacementL": "2.0", "Turbo": "", "EngineModel": "LFB",
              "ElectrificationLevel": "Strong HEV (Hybrid Electric Vehicle)"}
    assert parse_vpic(ACCORD_15T_VIN, payload(hybrid)).engine == "2.0L 4-cyl hybrid (LFB)"


def test_parse_warns_on_bad_check_digit() -> None:
    d = parse_vpic("1HGCV1F51JA000001", payload(ACCORD_15T))
    assert d.make == "Honda"  # still decoded...
    assert any("check digit" in w for w in d.warnings)  # ...but flagged as a likely typo


def test_parse_warns_when_nothing_decodes() -> None:
    d = parse_vpic(ACCORD_15T_VIN, payload(UNDECODABLE))
    assert d.make is None and d.year is None
    assert any("couldn't identify" in w for w in d.warnings)


# --- API endpoint (network mocked) --------------------------------------------------------


def use_vpic(handler) -> None:
    def client():
        with httpx.Client(transport=httpx.MockTransport(handler)) as c:
            yield c

    app.dependency_overrides[get_http_client] = client


def login(client: TestClient) -> None:
    assert client.post("/auth/register", json={"email": "vin@example.com", "password": "long enough pw"}).status_code == 201


def test_decode_endpoint_returns_proposal(client: TestClient) -> None:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, json=payload(ACCORD_15T))

    use_vpic(handler)
    login(client)
    response = client.get("/vehicles/decode-vin", params={"vin": "1hgcv1f55ja000001"})
    assert response.status_code == 200
    body = response.json()
    assert (body["make"], body["model"], body["trim"], body["source"]) == ("Honda", "Accord", "EX-L", "NHTSA vPIC")
    assert seen and ACCORD_15T_VIN in str(seen[0])
    assert client.get("/vehicles").json() == []  # decoding never saves anything


def test_decode_endpoint_rejects_bad_format_without_calling_nhtsa(client: TestClient) -> None:
    use_vpic(lambda request: pytest.fail("NHTSA should not be called"))
    login(client)
    assert client.get("/vehicles/decode-vin", params={"vin": "TOO-SHORT"}).status_code == 422


def test_decode_endpoint_reports_outage(client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    use_vpic(handler)
    login(client)
    response = client.get("/vehicles/decode-vin", params={"vin": ACCORD_15T_VIN})
    assert response.status_code == 502
    assert "manually" in response.json()["detail"]


def test_decode_endpoint_requires_login(client: TestClient) -> None:
    use_vpic(lambda request: pytest.fail("NHTSA should not be called"))
    assert client.get("/vehicles/decode-vin", params={"vin": ACCORD_15T_VIN}).status_code == 401


def test_saving_normalizes_vin_and_treats_blank_as_none(client: TestClient) -> None:
    login(client)
    saved = client.post("/vehicles", json={"vin": "1hgcv1f55 ja000001", "year": 2018, "make": "Honda", "model": "Accord"})
    assert saved.json()["vin"] == ACCORD_15T_VIN
    blank = client.post("/vehicles", json={"vin": "", "year": 2018, "make": "Honda", "model": "Civic"})
    assert blank.status_code == 201 and blank.json()["vin"] is None
