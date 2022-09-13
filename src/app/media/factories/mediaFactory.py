from ...media.models.database import models
from ...media.models.media import CreateImage, ViewImage


class MediaFactory:
    def create_image_entity_from_image(self, image):
        media_entity = models.Image(
                store=image.store,
                address=image.address,
                created=image.created,
                filename=image.filename,
                description=image.description,
                content_type=image.content_type,
                tags=image.tags)
        return media_entity

    def create_image_from_image_entity(self, image_entity):
        return CreateImage(
            id=image_entity.id,
            store=image_entity.store,
            address=image_entity.address,
            created=image_entity.created,
            filename=image_entity.filename,
            description=image_entity.description,
            content_type=image_entity.content_type,
            tags=image_entity.tags)

    def create_view_image_from_image_entity(self, image_entity):
        return ViewImage(
            id=image_entity.id,
            created=image_entity.created,
            description=image_entity.description,
            tags=image_entity.tags)
