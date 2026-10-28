"""Unit tests for upload validation, security, and endpoints."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.errors import PayloadTooLargeError, UnsupportedMediaError
from app.main import app
from app.models.base import get_db
from app.schemas.uploads import UploadRequest
from app.services.uploads import UploadService


@pytest.fixture
def mock_db_session():
    """Dummy session mock that doesn't hit a real database."""

    class DummySession:
        def add(self, obj):
            pass

        def flush(self):
            pass

        def close(self):
            pass

    return DummySession()


@pytest.fixture
def client(mock_db_session):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


def test_exe_renamed_to_jpg_rejected():
    service = UploadService()
    # Malicious .exe file extension
    req = UploadRequest(
        kind="photo",
        filename="malware.exe",
        mime="image/jpeg",
        size_bytes=1024,
    )
    with pytest.raises(UnsupportedMediaError) as exc_info:
        service.validate_upload(req)
    assert "prohibited" in str(exc_info.value).lower()


def test_disallowed_mime_rejected():
    service = UploadService()
    req = UploadRequest(
        kind="photo",
        filename="document.pdf",
        mime="application/pdf",
        size_bytes=1024,
    )
    with pytest.raises(UnsupportedMediaError) as exc_info:
        service.validate_upload(req)
    assert "unsupported" in str(exc_info.value).lower()


def test_photo_size_exceeded_rejected():
    service = UploadService()
    req = UploadRequest(
        kind="photo",
        filename="huge_photo.jpg",
        mime="image/jpeg",
        size_bytes=12 * 1024 * 1024,  # 12MB > 10MB limit
    )
    with pytest.raises(PayloadTooLargeError) as exc_info:
        service.validate_upload(req)
    assert "exceeds" in str(exc_info.value).lower()


def test_audio_size_exceeded_rejected():
    service = UploadService()
    req = UploadRequest(
        kind="audio",
        filename="long_recording.mp3",
        mime="audio/mpeg",
        size_bytes=30 * 1024 * 1024,  # 30MB > 25MB limit
    )
    with pytest.raises(PayloadTooLargeError) as exc_info:
        service.validate_upload(req)
    assert "exceeds" in str(exc_info.value).lower()


def test_valid_jpeg_returns_signed_url_with_tenant_prefixed_key():
    service = UploadService()
    b_id = uuid4()
    req = UploadRequest(
        kind="photo",
        filename="product_sample.jpg",
        mime="image/jpeg",
        size_bytes=2 * 1024 * 1024,  # 2MB
    )
    resp = service.create_upload_session(business_id=b_id, req=req)

    assert resp.media_id is not None
    assert resp.storage_key.startswith(f"{b_id}/uploads/")
    assert resp.storage_key.endswith(".jpg")
    assert resp.upload_url.startswith("http")
    assert resp.method == "PUT"
    assert resp.expires_in_seconds == 900


def test_post_uploads_api_endpoint(client):
    b_id = str(uuid4())
    headers = {
        "X-Business-ID": b_id,
        "X-User-ID": str(uuid4()),
        "X-User-Role": "owner",
    }
    payload = {
        "kind": "photo",
        "filename": "camera_snap.png",
        "mime": "image/png",
        "size_bytes": 500000,
    }
    response = client.post("/v1/uploads", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "upload_url" in data
    assert "media_id" in data
    assert data["storage_key"].startswith(f"{b_id}/uploads/")
