from io import BytesIO
from unittest import mock
from unittest.mock import call

import pytest
from fastapi import UploadFile
from fastapi_pagination import Page, Params
from openpyxl import Workbook
from starlette.datastructures import Headers
from starlette.responses import StreamingResponse

from src.app.worship.daos.songDAO import SongDAO
from src.app.worship.factories.songFactory import SongFactory
from src.app.worship.models.database import models
from src.app.worship.models.songs import CreateAuthor, CreateSong, ViewAuthor, ViewSong
from src.app.worship.services.songService import (
    NoAuthorException,
    NoSongException,
    RequiredColumnsNotPresentException,
    SongService,
    SongWithThatCodeExists,
)


def _build_service():
    return SongService(song_factory=SongFactory(), song_DAO=SongDAO())


@mock.patch.object(SongFactory, "create_song_from_song_entity")
@mock.patch.object(SongDAO, "get_all_songs")
def test_get_all_songs(mock_get_all, mock_create_song):
    service = _build_service()
    entity = models.Song(id=1, code="A1", name="Amazing Grace")
    mock_get_all.return_value = Page.create(items=[entity], total=1, params=Params(page=1, size=10))
    view = ViewSong(id=1, code="A1", name="Amazing Grace", authors=[])
    mock_create_song.return_value = view

    page = service.get_all_songs(Params(page=1, size=10))

    assert page.items == [view]


@mock.patch.object(SongDAO, "get_all_songs")
def test_get_all_songs_empty(mock_get_all):
    service = _build_service()
    mock_get_all.return_value = None
    assert service.get_all_songs() == []


@mock.patch.object(SongFactory, "create_song_from_song_entity")
@mock.patch.object(SongDAO, "get_song_by_id")
def test_get_song_by_id(mock_get_song, mock_create_song):
    service = _build_service()
    entity = models.Song(id=1, code="A1", name="Song")
    mock_get_song.return_value = entity
    view = ViewSong(id=1, code="A1", name="Song", authors=[])
    mock_create_song.return_value = view

    assert service.get_song_by_id(1) == view


@mock.patch.object(SongDAO, "get_song_by_id")
def test_get_song_by_id_missing(mock_get_song):
    service = _build_service()
    mock_get_song.return_value = None

    with pytest.raises(NoSongException):
        service.get_song_by_id(99)


@mock.patch.object(SongFactory, "create_song_from_song_entity")
@mock.patch.object(SongDAO, "create_song")
@mock.patch.object(SongFactory, "create_song_entity_from_song")
@mock.patch.object(SongDAO, "get_author_by_id")
@mock.patch.object(SongDAO, "get_song_by_code")
def test_create_song_with_authors(
    mock_get_by_code, mock_get_author, mock_create_entity, mock_create_song, mock_create_view
):
    service = _build_service()
    mock_get_by_code.return_value = None
    author = models.Author(id=2, name="Newton")
    mock_get_author.return_value = author
    entity = models.Song(id=1, code="A1", name="Amazing Grace")
    mock_create_entity.return_value = entity
    mock_create_song.return_value = entity
    view = ViewSong(id=1, code="A1", name="Amazing Grace", authors=[ViewAuthor(id=2, name="Newton")])
    mock_create_view.return_value = view

    result = service.create_song(CreateSong(code="A1", name="Amazing Grace", author_ids=[2]))

    assert result == view
    mock_create_entity.assert_called_once_with(
        CreateSong(code="A1", name="Amazing Grace", author_ids=[2]), [author]
    )


@mock.patch.object(SongDAO, "get_song_by_code")
def test_create_song_duplicate_code(mock_get_by_code):
    service = _build_service()
    mock_get_by_code.return_value = models.Song(id=1, code="A1", name="Existing")

    with pytest.raises(SongWithThatCodeExists):
        service.create_song(CreateSong(code="A1", name="New"))


@mock.patch.object(SongDAO, "get_author_by_id")
@mock.patch.object(SongDAO, "get_song_by_code")
def test_create_song_invalid_author(mock_get_by_code, mock_get_author):
    service = _build_service()
    mock_get_by_code.return_value = None
    mock_get_author.return_value = None

    with pytest.raises(NoAuthorException):
        service.create_song(CreateSong(code="A1", name="Song", author_ids=[99]))


@mock.patch.object(SongFactory, "create_author_from_author_entity")
@mock.patch.object(SongDAO, "create_author")
@mock.patch.object(SongFactory, "create_author_entity_from_author")
def test_create_author(mock_create_entity, mock_create_author, mock_create_view):
    service = _build_service()
    entity = models.Author(id=1, name="Newton")
    mock_create_entity.return_value = entity
    mock_create_author.return_value = entity
    view = ViewAuthor(id=1, name="Newton")
    mock_create_view.return_value = view

    assert service.create_author(CreateAuthor(name="Newton")) == view


@mock.patch.object(SongFactory, "create_author_from_author_entity")
@mock.patch.object(SongDAO, "update_author")
@mock.patch.object(SongDAO, "get_author_by_id")
def test_update_author(mock_get_author, mock_update_author, mock_create_view):
    service = _build_service()
    entity = models.Author(id=1, name="Old")
    mock_get_author.return_value = entity
    updated = models.Author(id=1, name="New")
    mock_update_author.return_value = updated
    view = ViewAuthor(id=1, name="New")
    mock_create_view.return_value = view

    result = service.update_author(1, CreateAuthor(name="New"))

    assert result == view
    mock_update_author.assert_called_once()


@mock.patch.object(SongDAO, "get_author_by_id")
def test_update_author_missing(mock_get_author):
    service = _build_service()
    mock_get_author.return_value = None

    with pytest.raises(NoAuthorException):
        service.update_author(1, CreateAuthor(name="New"))


@mock.patch.object(SongFactory, "create_author_from_author_entity")
@mock.patch.object(SongDAO, "get_all_authors")
def test_get_all_authors(mock_get_all, mock_create_view):
    service = _build_service()
    entity = models.Author(id=1, name="Newton")
    mock_get_all.return_value = [entity]
    view = ViewAuthor(id=1, name="Newton")
    mock_create_view.return_value = view

    assert service.get_all_authors() == [view]


@mock.patch.object(SongFactory, "create_author_from_author_entity")
@mock.patch.object(SongDAO, "get_author_by_id")
def test_get_author_by_id(mock_get_author, mock_create_view):
    service = _build_service()
    mock_get_author.return_value = models.Author(id=1, name="Newton")
    mock_create_view.return_value = ViewAuthor(id=1, name="Newton")

    assert service.get_author_by_id(1).name == "Newton"


@mock.patch.object(SongDAO, "get_author_by_id")
def test_get_author_by_id_missing(mock_get_author):
    service = _build_service()
    mock_get_author.return_value = None

    with pytest.raises(NoAuthorException):
        service.get_author_by_id(99)


@mock.patch.object(SongFactory, "create_song_from_song_entity")
@mock.patch.object(SongDAO, "update_song")
@mock.patch.object(SongDAO, "create_author_song")
@mock.patch.object(SongDAO, "delete_author_song")
@mock.patch.object(SongDAO, "get_existing_authors_for_song")
@mock.patch.object(SongDAO, "get_author_by_id")
@mock.patch.object(SongDAO, "get_song_by_id")
def test_update_song_replaces_authors(
    mock_get_song,
    mock_get_author,
    mock_get_existing,
    mock_delete_author_song,
    mock_create_author_song,
    mock_update_song,
    mock_create_view,
):
    service = _build_service()
    song_entity = models.Song(id=1, code="A1", name="Song")
    mock_get_song.return_value = song_entity
    author = models.Author(id=3, name="New Author")
    mock_get_author.return_value = author
    mock_get_existing.return_value = [models.AuthorSong(id=10, author_id=2, song_id=1)]
    mock_update_song.return_value = song_entity
    mock_create_view.return_value = ViewSong(id=1, code="A1", name="Song", authors=[])

    service.update_song(1, CreateSong(name="Song", author_ids=[3]))

    mock_delete_author_song.assert_called_once_with(10)
    mock_create_author_song.assert_called_once_with(song_entity, author)


@mock.patch.object(SongDAO, "get_song_by_id")
def test_update_song_missing(mock_get_song):
    service = _build_service()
    mock_get_song.return_value = None

    with pytest.raises(NoSongException):
        service.update_song(1, CreateSong(name="Song"))


@mock.patch.object(SongDAO, "get_author_by_id")
@mock.patch.object(SongDAO, "get_song_by_id")
def test_update_song_invalid_author(mock_get_song, mock_get_author):
    service = _build_service()
    mock_get_song.return_value = models.Song(id=1, code="A1", name="Song")
    mock_get_author.return_value = None

    with pytest.raises(NoAuthorException):
        service.update_song(1, CreateSong(name="Song", author_ids=[99]))


def test_create_song_from_row_maps_known_columns():
    service = _build_service()
    with mock.patch.object(SongService, "get_author_id_list", return_value=[1, 2]):
        create_song = service.create_song_from_row(
            {"NAME": 0, "CODE": 1, "AUTHOR": 2},
            ("Amazing Grace", "A1", "Newton"),
        )

    assert create_song.name == "Amazing Grace"
    assert create_song.code == "A1"
    assert create_song.author_ids == [1, 2]


@mock.patch.object(SongDAO, "get_author_by_name")
def test_get_author_id_list(mock_get_author_by_name):
    service = _build_service()
    mock_get_author_by_name.side_effect = [
        models.Author(id=1, name="Newton"),
        models.Author(id=2, name="Watts"),
    ]

    ids = service.get_author_id_list({"AUTHOR": 0}, ("Newton, Watts",))

    assert ids == [1, 2]


@mock.patch.object(SongDAO, "get_author_by_name")
def test_get_author_id_list_blank_author(mock_get_author_by_name):
    service = _build_service()
    assert service.get_author_id_list({"AUTHOR": 0}, ("",)) == []
    mock_get_author_by_name.assert_not_called()


def _xlsx_upload(rows, headers=("NAME", "AUTHOR", "CODE")):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(list(headers))
    for row in rows:
        sheet.append(list(row))
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return UploadFile(stream, filename="songs.xlsx", headers=Headers({
        "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }))


@mock.patch.object(SongService, "create_song")
@mock.patch.object(SongDAO, "create_author")
@mock.patch.object(SongFactory, "create_author_entity_from_author")
@mock.patch.object(SongDAO, "get_author_by_name")
@mock.patch.object(SongDAO, "get_song_by_code")
def test_upload_songs_creates_song_and_author(
    mock_get_song_by_code,
    mock_get_author_by_name,
    mock_create_author_entity,
    mock_create_author,
    mock_create_song,
):
    service = _build_service()
    mock_get_author_by_name.side_effect = [None, models.Author(id=1, name="Newton")]
    mock_create_author_entity.return_value = models.Author(name="Newton")
    mock_create_author.return_value = models.Author(id=1, name="Newton")
    mock_get_song_by_code.return_value = None
    mock_create_song.return_value = ViewSong(id=1, code="A1", name="Amazing Grace", authors=[])

    result = service.upload_songs(_xlsx_upload([("Amazing Grace", "Newton", "A1")]), False)

    assert "Songs created: 1" in result
    assert "Authors created: 1" in result
    mock_create_song.assert_called_once()


def test_upload_songs_requires_name_and_author_columns():
    service = _build_service()
    with pytest.raises(RequiredColumnsNotPresentException):
        service.upload_songs(_xlsx_upload([("A1",)], headers=("CODE",)), False)


@mock.patch.object(SongService, "update_song")
@mock.patch.object(SongFactory, "create_song_from_song_entity")
@mock.patch.object(SongDAO, "get_song_by_code")
@mock.patch.object(SongDAO, "get_author_by_name")
def test_upload_songs_updates_existing_by_code(
    mock_get_author_by_name, mock_get_song_by_code, mock_create_view, mock_update_song
):
    service = _build_service()
    mock_get_author_by_name.return_value = models.Author(id=1, name="Newton")
    existing = models.Song(id=5, code="A1", name="Old Name")
    mock_get_song_by_code.return_value = existing
    mock_create_view.return_value = ViewSong(id=5, code="A1", name="Old Name", authors=[])

    result = service.upload_songs(_xlsx_upload([("Amazing Grace", "Newton", "A1")]), False)

    assert "Songs updated: 1" in result
    mock_update_song.assert_called_once()


@mock.patch.object(SongDAO, "get_all_songs_without_pagination")
def test_export_songs_as_xlsx(mock_get_all):
    service = _build_service()
    author = models.Author(id=1, name="Newton")
    song = models.Song(id=1, code="A1", name="Amazing Grace", secondary_name=None, song_key="G", style=None, tempo=None, ccli_number=None, video_link=None)
    song.authors = [models.AuthorSong(id=1, author=author, song=song)]
    mock_get_all.return_value = [song]

    response = service.export_songs_as_xlsx()

    assert isinstance(response, StreamingResponse)
    assert "songs-" in response.headers["Content-Disposition"]
