from io import BytesIO

from fastapi import UploadFile
from starlette.datastructures import Headers

from src.app.utils.fileUtils import FileUtils


def test_use_jpg_content_type_converts_jpeg_header():
    file = UploadFile(BytesIO(b"img"), filename="photo.jpeg", headers=Headers({"content-type": "image/jpeg"}))
    assert file.content_type == "image/jpeg"

    FileUtils.use_jpg_content_type(file)

    assert file.content_type == "image/jpg"


def test_use_jpg_content_type_leaves_non_jpeg_unchanged():
    file = UploadFile(BytesIO(b"img"), filename="photo.png", headers=Headers({"content-type": "image/png"}))

    FileUtils.use_jpg_content_type(file)

    assert file.content_type == "image/png"


def test_get_file_extension_from_content_type():
    file = UploadFile(BytesIO(b"img"), filename="photo", headers=Headers({"content-type": "image/png"}))

    assert FileUtils.get_file_extension(file) == "png"


def test_get_file_extension_falls_back_to_filename():
    file = UploadFile(BytesIO(b"data"), filename="sheet.pdf", headers=Headers({"content-type": "application/x-unknown"}))

    extension = FileUtils.get_file_extension(file)

    assert extension == "pdf"


def test_get_file_extension_strips_leading_dot():
    file = UploadFile(BytesIO(b"img"), filename="photo.jpg", headers=Headers({"content-type": "image/jpeg"}))

    extension = FileUtils.get_file_extension(file)

    assert not extension.startswith(".")
    assert extension in ("jpg", "jpeg", "jpe")
