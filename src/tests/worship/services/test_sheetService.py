from io import BytesIO
from unittest import mock

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.database import models as media_models
from src.app.media.services.mediaService import MediaService
from src.app.worship.daos.sheetDAO import SheetDAO
from src.app.worship.daos.songDAO import SongDAO
from src.app.worship.factories.sheetFactory import SheetFactory
from src.app.worship.factories.songFactory import SongFactory
from src.app.worship.models.database import models
from src.app.worship.models.songs import SheetType, ViewSong
from src.app.worship.services.sheetService import NoSheetException, NoSongException, SheetService


def _build_service():
    return SheetService(
        sheet_factory=SheetFactory(),
        sheet_DAO=SheetDAO(),
        song_DAO=SongDAO(),
        media_service=MediaService(),
        media_factory=MediaFactory(),
        song_factory=SongFactory(),
    )


def _pdf_file():
    return UploadFile(
        BytesIO(b"%PDF"),
        filename="sheet.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )


@mock.patch.object(SongFactory, "create_song_from_song_entity")
@mock.patch.object(SheetDAO, "create_sheet")
@mock.patch.object(SheetFactory, "create_sheet_entity_from_details")
@mock.patch.object(MediaService, "upload_media_item")
@mock.patch.object(SongDAO, "get_song_by_id")
def test_upload_song_sheet(
    mock_get_song, mock_upload, mock_create_sheet_entity, mock_create_sheet, mock_create_song
):
    service = _build_service()
    song = models.Song(id=1, code="A1", name="Song", song_key="G")
    mock_get_song.side_effect = [song, song]
    media = media_models.MediaItem(id=9, store="local", address="a", created=__import__("datetime").datetime.now())
    mock_upload.return_value = media
    sheet_entity = models.Sheet(id=1, type="LYRICS", sheet_key="G", song_id=1, media_item_id=9)
    mock_create_sheet_entity.return_value = sheet_entity
    mock_create_song.return_value = ViewSong(id=1, code="A1", name="Song", authors=[])

    result = service.upload_song_sheet(1, "LYRICS", "G", _pdf_file())

    assert result.code == "A1"
    mock_upload.assert_called_once()
    assert mock_upload.call_args[0][1] == "A1_LYRICS_G.pdf"
    mock_create_sheet.assert_called_once_with(sheet_entity)


@mock.patch.object(SongDAO, "get_song_by_id")
def test_upload_song_sheet_missing_song(mock_get_song):
    service = _build_service()
    mock_get_song.return_value = None

    with pytest.raises(NoSongException):
        service.upload_song_sheet(1, "LYRICS", "G", _pdf_file())


@mock.patch.object(SongDAO, "get_song_by_id")
def test_upload_song_sheet_rejects_non_pdf(mock_get_song):
    service = _build_service()
    mock_get_song.return_value = models.Song(id=1, code="A1", name="Song")
    file = UploadFile(BytesIO(b"img"), filename="x.jpg", headers=Headers({"content-type": "image/jpeg"}))

    with pytest.raises(ValueError, match="Only PDF files are allowed"):
        service.upload_song_sheet(1, "LYRICS", "G", file)


@mock.patch.object(MediaService, "get_media_item_by_id")
@mock.patch.object(SheetDAO, "get_song_sheet")
@mock.patch.object(SongDAO, "get_song_by_id")
def test_get_song_sheet_uses_song_key_when_missing(mock_get_song, mock_get_sheet, mock_get_media):
    service = _build_service()
    song = models.Song(id=1, code="A1", name="Song", song_key="G")
    mock_get_song.return_value = song
    sheet = models.Sheet(id=1, type="LYRICS", sheet_key="G", song_id=1, media_item_id=9)
    mock_get_sheet.return_value = sheet
    mock_get_media.return_value = "file-response"

    result = service.get_song_sheet(1, "LYRICS", None)

    assert result == "file-response"
    mock_get_sheet.assert_called_once_with(1, "LYRICS", "G")
    mock_get_media.assert_called_once_with(9, as_attachment=False)


@mock.patch.object(SongDAO, "get_song_by_id")
def test_get_song_sheet_missing_song(mock_get_song):
    service = _build_service()
    mock_get_song.return_value = None

    with pytest.raises(NoSongException):
        service.get_song_sheet(1, "LYRICS", "G")


@mock.patch.object(SheetDAO, "get_song_sheet")
@mock.patch.object(SongDAO, "get_song_by_id")
def test_get_song_sheet_missing_sheet(mock_get_song, mock_get_sheet):
    service = _build_service()
    mock_get_song.return_value = models.Song(id=1, code="A1", name="Song", song_key="G")
    mock_get_sheet.return_value = None

    with pytest.raises(NoSongException):
        service.get_song_sheet(1, "LYRICS", "G")


def test_get_sheet_types():
    service = _build_service()
    assert service.get_sheet_types() == [t.value for t in SheetType]


@mock.patch.object(SongFactory, "create_song_from_song_entity")
@mock.patch.object(SheetDAO, "update_sheet")
@mock.patch.object(SheetDAO, "get_song_sheet")
@mock.patch.object(MediaService, "upload_media_item")
@mock.patch.object(SongDAO, "get_song_by_id")
def test_update_song_sheet(
    mock_get_song, mock_upload, mock_get_sheet, mock_update_sheet, mock_create_song
):
    service = _build_service()
    song = models.Song(id=1, code="A1", name="Song")
    mock_get_song.side_effect = [song, song]
    media = media_models.MediaItem(id=11, store="local", address="a", created=__import__("datetime").datetime.now())
    mock_upload.return_value = media
    sheet = models.Sheet(id=1, type="LYRICS", sheet_key="G", song_id=1, media_item_id=9)
    mock_get_sheet.return_value = sheet
    mock_create_song.return_value = ViewSong(id=1, code="A1", name="Song", authors=[])

    result = service.update_song_sheet(1, "LYRICS", "G", _pdf_file())

    assert result.code == "A1"
    assert sheet.media_item_id == 11
    mock_update_sheet.assert_called_once_with(sheet)


@mock.patch.object(SongDAO, "get_song_by_id")
def test_update_song_sheet_missing_song(mock_get_song):
    service = _build_service()
    mock_get_song.return_value = None

    with pytest.raises(NoSongException):
        service.update_song_sheet(1, "LYRICS", "G", _pdf_file())


@mock.patch.object(SheetDAO, "get_song_sheet")
@mock.patch.object(MediaService, "upload_media_item")
@mock.patch.object(SongDAO, "get_song_by_id")
def test_update_song_sheet_missing_sheet(mock_get_song, mock_upload, mock_get_sheet):
    service = _build_service()
    mock_get_song.return_value = models.Song(id=1, code="A1", name="Song")
    mock_upload.return_value = media_models.MediaItem(
        id=11, store="local", address="a", created=__import__("datetime").datetime.now()
    )
    mock_get_sheet.return_value = None

    with pytest.raises(NoSheetException):
        service.update_song_sheet(1, "LYRICS", "G", _pdf_file())
