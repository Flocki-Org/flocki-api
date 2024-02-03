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
