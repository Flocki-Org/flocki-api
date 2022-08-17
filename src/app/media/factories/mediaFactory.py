from ...media.models.database import models
from ...media.models.media import CreateImage

class MediaFactory:
    def createImageEntityFromImage(self, image):
        media_entity = models.Image(
                store=image.store,
                address=image.address,
                created=image.created,
                filename=image.filename,
                description=image.description,
                content_type=image.content_type,
                tags=image.tags)
        return media_entity

    def createImageFromImageEntity(self, image_entity):
        return CreateImage(
            id=image_entity.id,
            store=image_entity.store,
            address=image_entity.address,
            created=image_entity.created,
            filename=image_entity.filename,
            description=image_entity.description,
            content_type=image_entity.content_type,
            tags=image_entity.tags)
