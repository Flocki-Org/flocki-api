from fastapi import Depends

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from src.app.database import SessionLocal, get_db
from src.app.worship.models.database import models
from sqlalchemy import func, exc


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
        try:
            self.db.add(song)
            self.db.commit()
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Song with that code already exists")
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
        try:
            self.db.add(sheet)
            self.db.commit()
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Sheet with that type and key already exists")
        self.db.refresh(sheet)
        return sheet

    def get_song_by_code(self, code):
        return self.db.query(models.Song).filter(models.Song.code == code).first()

    def update_song(self, song_entity, update_values):
        if 'id' in update_values:
            del update_values['id']
        entity_to_update = self.db.query(models.Song).filter(models.Song.id == song_entity.id)
        entity_to_update.update(update_values)
        self.db.commit()
        return self.get_song_by_id(song_entity.id)

    def create_artist(self, artist_entity):
        try:
            self.db.add(artist_entity)
            self.db.commit()
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Artist with that name already exists")
        self.db.refresh(artist_entity)
        return artist_entity

    def update_artist(self, artist_entity, update_values):
        if 'id' in update_values:
            del update_values['id']
        entity_to_update = self.db.query(models.Artist).filter(models.Artist.id == artist_entity.id)
        entity_to_update.update(update_values)
        self.db.commit()
        return self.get_artist_by_id(artist_entity.id)

    def get_all_artists(self):
        return self.db.query(models.Artist).all()

    def get_artist_by_id(self, id):
        return self.db.query(models.Artist).filter(models.Artist.id == id).first()
