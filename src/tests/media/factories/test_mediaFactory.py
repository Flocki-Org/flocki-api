from datetime import datetime

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.database import models
from src.app.media.models.media import CreateMediaItem


def test_create_media_item_entity_from_media_item():
    factory = MediaFactory()
    media_item = CreateMediaItem(
        store="local",
        address="./media/a.jpg",
        created=datetime(2024, 1, 1),
        filename="a.jpg",
        description="desc",
        content_type="image/jpg",
        tags="profile,person",
    )

    entity = factory.create_media_item_entity_from_media_item(media_item)

    assert entity.store == "local"
    assert entity.filename == "a.jpg"
    assert entity.tags == "profile,person"


def test_create_media_item_from_media_item_entity():
    factory = MediaFactory()
    entity = models.MediaItem(
        id=5,
        store="s3",
        address="s3://bucket/a.jpg",
        created=datetime(2024, 2, 2),
        filename="a.jpg",
        description="desc",
        content_type="image/jpg",
        tags="tag",
    )

    media_item = factory.create_media_item_from_media_item_entity(entity)

    assert media_item.id == 5
    assert media_item.store == "s3"
    assert media_item.address == "s3://bucket/a.jpg"


def test_create_view_media_item_from_media_item_entity():
    factory = MediaFactory()
    entity = models.MediaItem(
        id=5,
        store="local",
        address="./a.jpg",
        created=datetime(2024, 2, 2),
        description="logo",
        tags="church",
    )

    view = factory.create_view_media_item_from_media_item_entity(entity)

    assert view.id == 5
    assert view.description == "logo"
    assert view.tags == "church"
    assert not hasattr(view, "address") or "address" not in view.model_dump()
