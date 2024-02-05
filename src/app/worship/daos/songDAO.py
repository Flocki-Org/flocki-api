from fastapi import Depends

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from src.app.database import SessionLocal, get_db
from src.app.worship.models.database import models
from sqlalchemy import func

class SongDAO:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def get_all_songs(self, params: Params = Params(page=1, size=100)) -> Page[models.Song]:
        return paginate(self.db.query(models.Song), params)

    def get_song_by_id(self, id) -> models.Song:
        return self.db.query(models.Song).filter(models.Song.id == id).first()

    def create_song(self, song: models.Song):
        if not song.code:
            song.code = self.get_next_code(song)
        self.db.add(song)
        self.db.commit()
        self.db.refresh(song)
        return song

    def get_next_code(self, song: models.Song):
        if not song.name:
            raise ValueError("Song name is required")
        first_char = song.name[0]
        # get the max code for the first character
        max_code = self.db.query(func.max(models.Song.code)).filter(models.Song.code.like(f"{first_char}%")).scalar()
        if not max_code:
            return f"{first_char}1"
        return f"{first_char}{int(max_code[1:]) + 1}"

    def create_sheet(self, sheet: models.Sheet):
        self.db.add(sheet)
        self.db.commit()
        self.db.refresh(sheet)
        return sheet
