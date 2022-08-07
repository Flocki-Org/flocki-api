from fastapi import Depends

from src.app.database import SessionLocal, get_db
from src.app.media.models.database import models


class MediaDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_image_by_id(self, id):
        return self.db.query(models.Image).filter(models.Image.id == id).first()

    def add_image(self, image):
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return self.get_image_by_id(image.id)
