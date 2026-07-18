"""Storage tests — R2 uploads are mocked; nothing here touches the network."""

import io
from unittest.mock import MagicMock

import pytest
from PIL import Image
from starlette.datastructures import Headers, UploadFile

from services.image_service import ImageService
from services.storage_service import StorageService, build_object_key


def test_build_object_key_uses_extension():
    key = build_object_key(".jpg")
    assert key.startswith("analyses/")
    assert key.endswith(".jpg")
    assert len(key) > len("analyses/.jpg")


def test_build_object_key_is_unguessable():
    keys = {build_object_key(".png") for _ in range(50)}
    assert len(keys) == 50


def test_upload_bytes_puts_object_and_returns_url(monkeypatch):
    fake_client = MagicMock()
    svc = StorageService()
    monkeypatch.setattr(svc, "_client", fake_client)
    monkeypatch.setattr(svc, "_bucket", "test-bucket")
    monkeypatch.setattr(svc, "_public_base_url", "https://pub.example.r2.dev")

    url = svc.upload_bytes(b"imagedata", ".png", "image/png")

    fake_client.put_object.assert_called_once()
    kwargs = fake_client.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "test-bucket"
    assert kwargs["Body"] == b"imagedata"
    assert kwargs["ContentType"] == "image/png"
    assert url.startswith("https://pub.example.r2.dev/analyses/")
    assert url.endswith(".png")


def _png_upload(name="ref.png", content_type="image/png"):
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), (10, 20, 30)).save(buf, format="PNG")
    buf.seek(0)
    return UploadFile(
        file=buf, filename=name, headers=Headers({"content-type": content_type})
    )


def _image_service_with_fake_storage(monkeypatch):
    svc = ImageService()
    fake_storage = MagicMock()
    fake_storage.upload_bytes.return_value = "https://pub.example.r2.dev/analyses/abc.png"
    monkeypatch.setattr(svc, "_storage", fake_storage)
    return svc, fake_storage


@pytest.mark.asyncio
async def test_save_upload_returns_r2_url(monkeypatch):
    svc, fake_storage = _image_service_with_fake_storage(monkeypatch)

    url = await svc.save_upload(_png_upload())

    assert url == "https://pub.example.r2.dev/analyses/abc.png"
    fake_storage.upload_bytes.assert_called_once()


@pytest.mark.asyncio
async def test_save_upload_rejects_bad_content_type(monkeypatch):
    svc, fake_storage = _image_service_with_fake_storage(monkeypatch)

    with pytest.raises(ValueError):
        await svc.save_upload(_png_upload(content_type="application/pdf"))
    fake_storage.upload_bytes.assert_not_called()


@pytest.mark.asyncio
async def test_save_upload_rejects_oversize_file(monkeypatch):
    svc, fake_storage = _image_service_with_fake_storage(monkeypatch)
    monkeypatch.setattr(svc, "max_bytes", 10)

    with pytest.raises(ValueError):
        await svc.save_upload(_png_upload())
    fake_storage.upload_bytes.assert_not_called()
