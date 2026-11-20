import io
from pathlib import Path

import pillow_heif
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import config
from app.main import app
from app.storage import LocalStorage, get_storage
from app.uploads import UnsupportedFile, prepare, sniff_type

pillow_heif.register_heif_opener()

PDF = b"%PDF-1.4\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n"


def image_bytes(fmt: str, size=(60, 40)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, "green").save(out, format=fmt)
    return out.getvalue()


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    store = LocalStorage(tmp_path / "uploads")
    app.dependency_overrides[get_storage] = lambda: store
    return store


def login_with_vehicle(client: TestClient, email: str = "docs@example.com") -> int:
    client.post("/auth/register", json={"email": email, "password": "long enough pw"})
    return client.post("/vehicles", json={"year": 2018, "make": "Honda", "model": "Accord"}).json()["id"]


def upload(client: TestClient, vehicle_id: int, *files: tuple[str, bytes, str], note: str | None = None):
    return client.post(
        f"/vehicles/{vehicle_id}/documents",
        files=[("files", f) for f in files],
        data={"note": note} if note else None,
    )


# --- file type detection & conversion -------------------------------------------------------


def test_sniff_type_uses_contents_not_names() -> None:
    assert sniff_type(PDF) == "application/pdf"
    assert sniff_type(image_bytes("JPEG")) == "image/jpeg"
    assert sniff_type(image_bytes("PNG")) == "image/png"
    assert sniff_type(image_bytes("HEIF")) == "image/heic"
    assert sniff_type(b"MZ\x90\x00 not a document") is None


def test_heic_is_converted_to_jpeg_and_original_kept() -> None:
    heic = image_bytes("HEIF")
    prepared = prepare(heic)
    assert prepared.content_type == "image/jpeg" and sniff_type(prepared.data) == "image/jpeg"
    assert prepared.original == heic and prepared.original_content_type == "image/heic"


def test_prepare_rejects_empty_and_unknown() -> None:
    with pytest.raises(UnsupportedFile, match="empty"):
        prepare(b"")
    with pytest.raises(UnsupportedFile, match="Unsupported"):
        prepare(b"just some text")


# --- API ------------------------------------------------------------------------------------


def test_upload_multi_page_document_and_list_it(client: TestClient, storage: LocalStorage) -> None:
    vehicle_id = login_with_vehicle(client)
    response = upload(
        client,
        vehicle_id,
        ("invoice.pdf", PDF, "application/pdf"),
        ("page2.HEIC", image_bytes("HEIF"), "image/heic"),
        ("page3.png", image_bytes("PNG"), "image/png"),
        note="Oil change at dealer",
    )
    assert response.status_code == 201, response.text
    document = response.json()
    assert document["note"] == "Oil change at dealer"
    assert document["extraction_status"] == "pending"
    assert [f["original_filename"] for f in document["files"]] == ["invoice.pdf", "page2.HEIC", "page3.png"]
    assert [f["content_type"] for f in document["files"]] == ["application/pdf", "image/jpeg", "image/png"]
    assert document["files"][1]["converted_from"] == "image/heic"

    # 3 stored files + 1 HEIC original, all under this vehicle's folder.
    stored = [p for p in storage.root.rglob("*") if p.is_file()]
    assert len(stored) == 4
    assert all(f"vehicles/{vehicle_id}/documents/{document['id']}" in str(p) for p in stored)

    listed = client.get(f"/vehicles/{vehicle_id}/documents").json()
    assert [d["id"] for d in listed] == [document["id"]]


def test_download_returns_the_stored_file(client: TestClient, storage: LocalStorage) -> None:
    vehicle_id = login_with_vehicle(client)
    heic = image_bytes("HEIF")
    document = upload(client, vehicle_id, ("a.pdf", PDF, "application/pdf"), ("b.heic", heic, "image/heic")).json()
    pdf_file, photo = document["files"]

    pdf = client.get(f"/documents/{document['id']}/files/{pdf_file['id']}")
    assert pdf.status_code == 200 and pdf.content == PDF
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.headers["x-content-type-options"] == "nosniff"

    jpeg = client.get(f"/documents/{document['id']}/files/{photo['id']}")
    assert jpeg.headers["content-type"] == "image/jpeg"
    assert 'filename="b.jpg"' in jpeg.headers["content-disposition"]
    original = client.get(f"/documents/{document['id']}/files/{photo['id']}", params={"original": "true"})
    assert original.content == heic

    # The PDF has no converted original.
    assert client.get(f"/documents/{document['id']}/files/{pdf_file['id']}", params={"original": "true"}).status_code == 404


def test_bad_file_rejects_whole_upload(client: TestClient, storage: LocalStorage) -> None:
    vehicle_id = login_with_vehicle(client)
    response = upload(
        client, vehicle_id, ("ok.pdf", PDF, "application/pdf"), ("virus.pdf", b"MZ not really a pdf", "application/pdf")
    )
    assert response.status_code == 415
    assert "virus.pdf" in response.json()["detail"]
    assert client.get(f"/vehicles/{vehicle_id}/documents").json() == []
    assert not storage.root.exists() or not any(p.is_file() for p in storage.root.rglob("*"))


def test_file_size_limit(client: TestClient, storage: LocalStorage, monkeypatch: pytest.MonkeyPatch) -> None:
    import app.routers.documents as documents_router

    monkeypatch.setattr(documents_router, "MAX_UPLOAD_BYTES", 100)
    vehicle_id = login_with_vehicle(client)
    response = upload(client, vehicle_id, ("big.pdf", PDF + b" " * 200, "application/pdf"))
    assert response.status_code == 413


def test_default_limit_is_20_mb() -> None:
    assert config.MAX_UPLOAD_BYTES == 20 * 1024 * 1024


def test_other_users_cannot_upload_list_or_download(
    client: TestClient, other_client: TestClient, storage: LocalStorage
) -> None:
    alice_vehicle = login_with_vehicle(client, "alice@example.com")
    document = upload(client, alice_vehicle, ("a.pdf", PDF, "application/pdf")).json()
    file_id = document["files"][0]["id"]

    login_with_vehicle(other_client, "bob@example.com")
    assert upload(other_client, alice_vehicle, ("x.pdf", PDF, "application/pdf")).status_code == 404
    assert other_client.get(f"/vehicles/{alice_vehicle}/documents").status_code == 404
    assert other_client.get(f"/documents/{document['id']}/files/{file_id}").status_code == 404


def test_storage_rejects_path_escape(tmp_path: Path) -> None:
    store = LocalStorage(tmp_path)
    with pytest.raises(ValueError):
        store.path_for("../../etc/passwd")
