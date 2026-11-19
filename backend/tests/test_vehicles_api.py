from fastapi.testclient import TestClient

ACCORD = {"vin": "1hgcv1f3xja000000", "year": 2018, "make": "Honda", "model": "Accord"}


def login_as(client: TestClient, email: str) -> None:
    response = client.post("/auth/register", json={"email": email, "password": "long enough pw"})
    assert response.status_code == 201


def test_create_list_and_get_own_vehicle(client: TestClient) -> None:
    login_as(client, "owner@example.com")
    created = client.post("/vehicles", json=ACCORD)
    assert created.status_code == 201
    vehicle = created.json()
    assert vehicle["vin"] == "1HGCV1F3XJA000000"  # uppercased
    assert vehicle["trim"] is None

    assert [v["id"] for v in client.get("/vehicles").json()] == [vehicle["id"]]
    assert client.get(f"/vehicles/{vehicle['id']}").json()["model"] == "Accord"


def test_users_cannot_see_each_others_vehicles(client: TestClient, other_client: TestClient) -> None:
    login_as(client, "alice@example.com")
    login_as(other_client, "bob@example.com")

    alice_car = client.post("/vehicles", json=ACCORD).json()
    bob_car = other_client.post("/vehicles", json={**ACCORD, "model": "Civic"}).json()

    # Each list contains only the owner's car.
    assert [v["id"] for v in client.get("/vehicles").json()] == [alice_car["id"]]
    assert [v["id"] for v in other_client.get("/vehicles").json()] == [bob_car["id"]]

    # Direct access to the other user's car looks like it doesn't exist.
    assert other_client.get(f"/vehicles/{alice_car['id']}").status_code == 404
    assert client.get(f"/vehicles/{bob_car['id']}").status_code == 404


def test_duplicate_vin_for_same_user_is_conflict(client: TestClient) -> None:
    login_as(client, "owner@example.com")
    client.post("/vehicles", json=ACCORD)
    assert client.post("/vehicles", json=ACCORD).status_code == 409


def test_invalid_vehicle_rejected(client: TestClient) -> None:
    login_as(client, "owner@example.com")
    assert client.post("/vehicles", json={**ACCORD, "vin": "SHORT"}).status_code == 422
    assert client.post("/vehicles", json={**ACCORD, "purchase_mileage": -5}).status_code == 422
