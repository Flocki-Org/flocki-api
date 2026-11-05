from datetime import datetime
from io import BytesIO
from unittest import mock

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers
from starlette.responses import FileResponse, StreamingResponse

from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.database import models
from src.app.media.models.media import CreateMediaItem
from src.app.media.services.mediaService import (
    MediaService,
    NoMediaItemException,
    UnsupportedMediaItemStoreException,
)
from src.app.utils.s3Utils import S3Utils


def _service():
    with mock.patch("src.app.utils.s3Utils.boto3.resource"):
        return MediaService(media_DAO=MediaDAO(), media_factory=MediaFactory())


def test_get_media_item_by_id_local_attachment(tmp_path):
    service = _service()
    media_path = tmp_path / "photo.jpg"
    media_path.write_bytes(b"img")
    with mock.patch.object(MediaDAO, "get_media_item_by_id") as mock_get_media:
        mock_get_media.return_value = models.MediaItem(
            id=1,
            store="local",
            address=str(media_path),
            filename="photo.jpg",
            content_type="image/jpg",
            created=datetime.now(),
        )
        response = service.get_media_item_by_id(1, as_attachment=True)

    assert isinstance(response, FileResponse)
    assert response.path == str(media_path)
    assert "attachment" in response.headers["Content-Disposition"]


def test_get_media_item_by_id_local_inline(tmp_path):
    service = _service()
    media_path = tmp_path / "photo.jpg"
    media_path.write_bytes(b"img")
    with mock.patch.object(MediaDAO, "get_media_item_by_id") as mock_get_media:
        mock_get_media.return_value = models.MediaItem(
            id=1,
            store="local",
            address=str(media_path),
            filename="photo.jpg",
            content_type="image/jpg",
            created=datetime.now(),
        )
        response = service.get_media_item_by_id(1, as_attachment=False)

    assert "inline" in response.headers["Content-Disposition"]


def test_get_media_item_by_id_missing():
    service = _service()
    with mock.patch.object(MediaDAO, "get_media_item_by_id", return_value=None):
        with pytest.raises(NoMediaItemException):
            service.get_media_item_by_id(99)


def test_get_media_item_by_id_missing_local_file():
    service = _service()
    with mock.patch.object(MediaDAO, "get_media_item_by_id") as mock_get_media:
        mock_get_media.return_value = models.MediaItem(
            id=1, store="local", address="/missing.jpg", filename="missing.jpg", created=datetime.now()
        )
        with pytest.raises(NoMediaItemException):
            service.get_media_item_by_id(1)


def test_get_media_item_by_id_s3():
    service = _service()
    with mock.patch.object(MediaDAO, "get_media_item_by_id") as mock_get_media, \
            mock.patch.object(S3Utils, "get_file") as mock_get_file:
        mock_get_media.return_value = models.MediaItem(
            id=1,
            store="s3",
            address="s3://bucket/file.pdf",
            filename="file.pdf",
            content_type="application/pdf",
            created=datetime.now(),
        )
        body = mock.Mock()
        body.iter_chunks.return_value = iter([b"chunk"])
        mock_get_file.return_value = {"Body": body, "Key": "file.pdf"}

        response = service.get_media_item_by_id(1)

    assert isinstance(response, StreamingResponse)
    mock_get_file.assert_called_once_with("file.pdf")


def test_get_media_item_by_id_unsupported_store():
    service = _service()
    with mock.patch.object(MediaDAO, "get_media_item_by_id") as mock_get_media:
        mock_get_media.return_value = models.MediaItem(
            id=1, store="gcs", address="x", filename="x", created=datetime.now()
        )
        with pytest.raises(NotImplementedError):
            service.get_media_item_by_id(1)


def test_upload_media_item_local(tmp_path):
    service = _service()
    file = UploadFile(BytesIO(b"bytes"), filename="photo.jpg", headers=Headers({"content-type": "image/jpg"}))
    entity = models.MediaItem(id=1, store="local", address=str(tmp_path / "photo.jpg"), created=datetime.now())

    with mock.patch("src.app.media.services.mediaService.settings") as mock_settings, \
            mock.patch.object(MediaFactory, "create_media_item_entity_from_media_item", return_value=entity) as mock_create_entity, \
            mock.patch.object(MediaDAO, "add_media_item", return_value=entity) as mock_add_media:
        mock_settings.flocki_media_store = "local"
        mock_settings.flocki_media_base_path = str(tmp_path)
        mock_settings.flocki_s3_region_name = "eu-west-1"
        mock_settings.flocki_s3_bucket_name = "bucket"
        mock_settings.flocki_s3_access_key = ""
        mock_settings.flocki_s3_secret_access_key = ""

        result = service.upload_media_item(file, "photo.jpg", "desc")

    assert result.id == 1
    assert (tmp_path / "photo.jpg").read_bytes() == b"bytes"
    mock_add_media.assert_called_once()
    create_arg = mock_create_entity.call_args[0][0]
    assert create_arg.store == "local"
    assert create_arg.address.endswith("photo.jpg")


def test_upload_media_item_s3():
    service = _service()
    file = UploadFile(BytesIO(b"bytes"), filename="photo.jpg", headers=Headers({"content-type": "image/jpg"}))
    entity = models.MediaItem(id=2, store="s3", address="s3://bucket/photo.jpg", created=datetime.now())

    with mock.patch("src.app.media.services.mediaService.settings") as mock_settings, \
            mock.patch.object(S3Utils, "upload_file", return_value=True), \
            mock.patch.object(MediaFactory, "create_media_item_entity_from_media_item", return_value=entity) as mock_create_entity, \
            mock.patch.object(MediaDAO, "add_media_item", return_value=entity):
        mock_settings.flocki_media_store = "s3"
        mock_settings.flocki_s3_bucket_name = "bucket"
        mock_settings.flocki_media_base_path = "./media"
        mock_settings.flocki_s3_region_name = "eu-west-1"
        mock_settings.flocki_s3_access_key = ""
        mock_settings.flocki_s3_secret_access_key = ""

        result = service.upload_media_item(file, "photo.jpg", "desc")

    assert result.store == "s3"
    create_arg = mock_create_entity.call_args[0][0]
    assert create_arg.address == "s3://bucket/photo.jpg"


def test_upload_media_item_s3_failure():
    service = _service()
    file = UploadFile(BytesIO(b"bytes"), filename="photo.jpg", headers=Headers({"content-type": "image/jpg"}))

    with mock.patch("src.app.media.services.mediaService.settings") as mock_settings, \
            mock.patch.object(S3Utils, "upload_file", return_value=False):
        mock_settings.flocki_media_store = "s3"
        mock_settings.flocki_s3_bucket_name = "bucket"
        mock_settings.flocki_media_base_path = "./media"
        mock_settings.flocki_s3_region_name = "eu-west-1"
        mock_settings.flocki_s3_access_key = ""
        mock_settings.flocki_s3_secret_access_key = ""

        with pytest.raises(Exception, match="File upload failed"):
            service.upload_media_item(file, "photo.jpg")


def test_upload_media_item_unsupported_store():
    service = _service()
    file = UploadFile(BytesIO(b"bytes"), filename="photo.jpg", headers=Headers({"content-type": "image/jpg"}))

    with mock.patch("src.app.media.services.mediaService.settings") as mock_settings:
        mock_settings.flocki_media_store = "azure"
        mock_settings.flocki_media_base_path = "./media"
        mock_settings.flocki_s3_region_name = "eu-west-1"
        mock_settings.flocki_s3_bucket_name = "bucket"
        mock_settings.flocki_s3_access_key = ""
        mock_settings.flocki_s3_secret_access_key = ""

        with pytest.raises(UnsupportedMediaItemStoreException):
            service.upload_media_item(file, "photo.jpg")


def test_create_media_item():
    service = _service()
    entity = models.MediaItem(id=1, store="local", address="a", created=datetime.now())
    expected = CreateMediaItem(id=1, store="local", address="a", created=datetime.now())
    file = UploadFile(BytesIO(b"bytes"), filename="photo.jpg", headers=Headers({"content-type": "image/jpg"}))

    with mock.patch.object(MediaService, "upload_media_item", return_value=entity) as mock_upload, \
            mock.patch.object(MediaFactory, "create_media_item_from_media_item_entity", return_value=expected):
        result = service.create_media_item(file, "photo.jpg", "desc")

    assert result == expected
    mock_upload.assert_called_once_with(file, "photo.jpg", "desc")


def test_upload_image_normalizes_jpeg():
    service = _service()
    file = UploadFile(BytesIO(b"bytes"), filename="photo.jpeg", headers=Headers({"content-type": "image/jpeg"}))
    entity = models.MediaItem(id=1, store="local", address="a", created=datetime.now())

    with mock.patch.object(MediaService, "upload_media_item", return_value=entity) as mock_upload, \
            mock.patch("src.app.media.services.mediaService.FileUtils.use_jpg_content_type") as mock_use_jpg:
        result = service.upload_image(file, "photo.jpg", "profile")

    assert result == entity
    mock_use_jpg.assert_called_once_with(file)
    mock_upload.assert_called_once_with(file, "photo.jpg", "profile")
