from datetime import datetime

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.database import models as media_models
from src.app.worship.factories.sheetFactory import SheetFactory
from src.app.worship.models.database import models
from src.app.worship.models.songs import CreateSheet, SheetType


def test_create_sheet_entity_from_sheet():
    factory = SheetFactory(media_factory=MediaFactory())
    sheet = CreateSheet(type=SheetType.LYRICS, song_id=1, sheet_key="G", media_item_id=9)

    entity = factory.create_sheet_entity_from_sheet(sheet)

    assert entity.type == SheetType.LYRICS
    assert entity.song_id == 1
    assert entity.sheet_key == "G"
    assert entity.media_item_id == 9


def test_create_sheet_from_sheet_entity_none():
    factory = SheetFactory(media_factory=MediaFactory())
    assert factory.create_sheet_from_sheet_entity(None) is None


def test_create_sheet_from_sheet_entity():
    factory = SheetFactory(media_factory=MediaFactory())
    media = media_models.MediaItem(
        id=9, store="local", address="a", created=datetime.now(), description="lyrics sheet"
    )
    entity = models.Sheet(id=3, type="LYRICS", sheet_key="G", song_id=1, media_item_id=9, media_item=media)

    view = factory.create_sheet_from_sheet_entity(entity)

    assert view.id == 3
    assert view.song_id == 1
    assert view.sheet_key == "G"
    assert view.media_item.id == 9
    assert view.media_item.description == "lyrics sheet"


def test_create_sheet_entity_from_details():
    factory = SheetFactory(media_factory=MediaFactory())
    song = models.Song(id=4, code="A1", name="Song")

    entity = factory.create_sheet_entity_from_details(song, "GUITAR", "A", 12)

    assert entity.song_id == 4
    assert entity.type == "GUITAR"
    assert entity.sheet_key == "A"
    assert entity.media_item_id == 12
