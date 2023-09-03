from fastapi import Depends

from src.app.database import SessionLocal, get_db
from src.app.media.models.database import models


class MediaDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_media_item_by_id(self, id):
        return self.db.query(models.MediaItem).filter(models.MediaItem.id == id).first()

    def add_media_item(self, media_item):
        self.db.add(media_item)
        self.db.commit()
        self.db.refresh(media_item)
        return self.get_media_item_by_id(media_item.id)
