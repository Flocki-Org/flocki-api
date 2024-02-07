from typing import List

from fastapi import Depends

from src.app.database import SessionLocal, get_db
from src.app.worship.models.database import models
from sqlalchemy import func, exc


class SheetDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_all_sheets_for_song(self, song_id) -> List[models.Sheet]:
        return self.db.query(models.Song).filter(models.Sheet.song_id == song_id).all()

    def get_sheet_by_id(self, id) -> models.Sheet:
        return self.db.query(models.Sheet).filter(models.Sheet.id == id).first()

    def create_sheet(self, sheet: models.Sheet):
        try:
            self.db.add(sheet)
            self.db.commit()
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Sheet with that type and key already exists")
        self.db.refresh(sheet)
        return sheet

    def get_song_sheet(self, song_id, type, sheet_key):
        return self.db.query(models.Sheet).filter(
            models.Sheet.song_id == song_id, models.Sheet.type == type, models.Sheet.sheet_key == sheet_key).first()
