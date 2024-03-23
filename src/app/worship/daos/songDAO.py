from typing import List

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
        #order by code
        return paginate(self.db.query(models.Song).order_by(models.Song.code), params)

    def get_all_songs_without_pagination(self) -> List[models.Song]:
        return self.db.query(models.Song).order_by(models.Song.code)

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

    def create_author(self, author_entity):
        try:
            self.db.add(author_entity)
            self.db.commit()
        except exc.IntegrityError:
            self.db.rollback()
            raise ValueError("Author with that name already exists")
        self.db.refresh(author_entity)
        return author_entity

    def update_author(self, author_entity, update_values):
        if 'id' in update_values:
            del update_values['id']
        entity_to_update = self.db.query(models.Author).filter(models.Author.id == author_entity.id)
        entity_to_update.update(update_values)
        self.db.commit()
        return self.get_author_by_id(author_entity.id)

    def get_all_authors(self):
        return self.db.query(models.Author).all()

    def get_author_by_id(self, id):
        return self.db.query(models.Author).filter(models.Author.id == id).first()

    def get_authors_by_ids(self, author_ids):
        return self.db.query(models.Author).filter(models.Author.id.in_(author_ids)).all()

    def get_existing_authors_for_song(self, song_id):
        return self.db.query(models.AuthorSong).filter(models.AuthorSong.song_id == song_id).all()

    def delete_author_song(self, id):
        self.db.query(models.AuthorSong).filter(models.AuthorSong.id == id).delete(synchronize_session=False)

    def create_author_song(self, song_entity, author):
        self.db.add(models.AuthorSong(
            song=song_entity,
            author=author
        ))

    def get_author_by_name(self, author_name):
        # ignore case
        return self.db.query(models.Author).filter(func.lower(models.Author.name) == func.lower(author_name)).first()

    def get_song_by_name(self, param):
        # ignore case
        return self.db.query(models.Song).filter(func.lower(models.Song.name) == func.lower(param)).first()
