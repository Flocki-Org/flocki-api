from fastapi import Depends

from ...media.factories.mediaFactory import MediaFactory
from ...worship.models.songs import CreateSheet, ViewSheet
from ...worship.models.database import models

class SheetFactory:

        def __init__(self, media_factory: MediaFactory = Depends(MediaFactory)):
            self.media_factory = media_factory

        def create_sheet_entity_from_sheet(self, sheet):
            sheet_entity = models.Sheet(
                    type=sheet.type,
                    song_id=sheet.song_id,
                    media_item_id=sheet.media_item_id,
                    sheet_key=sheet.sheet_key)
            return sheet_entity

        def create_sheet_from_sheet_entity(self, sheet_entity: models.Sheet) -> ViewSheet:
            if sheet_entity is None:
                return None

            media_item = self.media_factory.create_media_item_from_media_item_entity(sheet_entity.media_item)

            return ViewSheet(
                id=sheet_entity.id,
                type=sheet_entity.type,
                song_id=sheet_entity.song_id,
                media_item=media_item,
                sheet_key=sheet_entity.sheet_key)

        def create_sheet_entity_from_details(self, song: models.Song, type: str, sheet_key: str, media_item_id: int):
            sheet_entity = models.Sheet(
                type=type,
                song_id=song.id,
                media_item_id=media_item_id,
                sheet_key=sheet_key)
            return sheet_entity
