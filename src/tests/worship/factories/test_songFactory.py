from datetime import datetime
from unittest import mock

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.database import models as media_models
from src.app.media.models.media import CreateMediaItem
from src.app.worship.factories.sheetFactory import SheetFactory
from src.app.worship.factories.songFactory import SongFactory
from src.app.worship.models.database import models
from src.app.worship.models.songs import CreateAuthor, CreateSong, ViewSheet
import pytest


def test_create_song_entity_from_song_with_authors():
    factory = SongFactory(sheet_factory=SheetFactory(media_factory=MediaFactory()))
    authors = [models.Author(id=1, name="Newton"), models.Author(id=2, name="Watts")]
    song = CreateSong(code="A1", name="Amazing Grace", song_key="G", author_ids=[1, 2])

    entity = factory.create_song_entity_from_song(song, authors)

    assert entity.code == "A1"
    assert entity.name == "Amazing Grace"
    assert len(entity.authors) == 2
    assert entity.authors[0].author.name == "Newton"


def test_create_song_from_song_entity():
    sheet_factory = SheetFactory(media_factory=MediaFactory())
    factory = SongFactory(sheet_factory=sheet_factory)
    song_entity = models.Song(id=1, code="A1", name="Amazing Grace", song_key="G")
    media = media_models.MediaItem(id=9, store="local", address="a", created=datetime.now(), filename="a.pdf")
    sheet = models.Sheet(id=3, type="LYRICS", sheet_key="G", song_id=1, media_item_id=9, media_item=media)
    song_entity.sheets = [sheet]
    author = models.Author(id=2, name="Newton")
    song_entity.authors = [models.AuthorSong(id=1, author=author, song=song_entity)]

    with mock.patch.object(
        SheetFactory,
        "create_sheet_from_sheet_entity",
        return_value=ViewSheet(id=3, type="LYRICS", sheet_key="G", song_id=1),
    ):
        view = factory.create_song_from_song_entity(song_entity)

    assert view.id == 1
    assert view.code == "A1"
    assert len(view.authors) == 1
    assert view.authors[0].name == "Newton"
    assert len(view.sheets) == 1


def test_create_song_from_song_entity_rejects_none():
    factory = SongFactory(sheet_factory=SheetFactory(media_factory=MediaFactory()))
    with pytest.raises(ValueError):
        factory.create_song_from_song_entity(None)


def test_create_author_entity_and_view():
    factory = SongFactory(sheet_factory=SheetFactory(media_factory=MediaFactory()))
    entity = factory.create_author_entity_from_author(CreateAuthor(name="Newton"))
    assert entity.name == "Newton"

    entity.id = 5
    view = factory.create_author_from_author_entity(entity)
    assert view.id == 5
    assert view.name == "Newton"


def test_create_author_rejects_none():
    factory = SongFactory(sheet_factory=SheetFactory(media_factory=MediaFactory()))
    with pytest.raises(ValueError):
        factory.create_author_entity_from_author(None)
    with pytest.raises(ValueError):
        factory.create_author_from_author_entity(None)
