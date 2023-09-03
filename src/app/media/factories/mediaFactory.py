from ...media.models.database import models
from ...media.models.media import CreateMediaItem, ViewMediaItem


class MediaFactory:
    def create_media_item_entity_from_media_item(self, media_item) -> models.MediaItem:
        media_entity = models.MediaItem(
                store=media_item.store,
                address=media_item.address,
                created=media_item.created,
                filename=media_item.filename,
                description=media_item.description,
                content_type=media_item.content_type,
                tags=media_item.tags)
        return media_entity

    def create_media_item_from_media_item_entity(self, media_item_entity):
        return CreateMediaItem(
            id=media_item_entity.id,
            store=media_item_entity.store,
            address=media_item_entity.address,
            created=media_item_entity.created,
            filename=media_item_entity.filename,
            description=media_item_entity.description,
            content_type=media_item_entity.content_type,
            tags=media_item_entity.tags)

    def create_view_media_item_from_media_item_entity(self, media_item_entity):
        return ViewMediaItem(
            id=media_item_entity.id,
            created=media_item_entity.created,
            description=media_item_entity.description,
            tags=media_item_entity.tags)
