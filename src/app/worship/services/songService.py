from fastapi import Depends

from fastapi_pagination import Page, Params
from openpyxl import load_workbook
from src.app.worship.daos.songDAO import SongDAO
from src.app.worship.models.database.models import Song
from src.app.worship.factories.songFactory import SongFactory
from src.app.worship.models.songs import ViewSong, CreateAuthor, ViewAuthor, CreateSong


class NoSongException (Exception):
    pass


class SongWithThatCodeExists (Exception):
    pass


class NoAuthorException(Exception):
    pass


class RequiredColumnsNotPresentException(Exception):
    pass


class SongService:
    def __init__(self, song_factory: SongFactory = Depends(SongFactory), song_DAO: SongDAO = Depends(SongDAO)):
        self.song_factory = song_factory
        self.song_DAO = song_DAO

    def get_all_songs(self, params: Params = Params(page=1, size=100)) -> Page[ViewSong]:
        song_entities = []
        song_entities_page = self.song_DAO.get_all_songs(params)
        if song_entities_page:
            for song_entity in song_entities_page.items:
                song_entities.append(self.song_factory.create_song_from_song_entity(song_entity))

            return Page.create(items=song_entities, params=params, total=song_entities_page.total)
        else:
            return []

    def get_song_by_id(self, id) -> ViewSong:
        song_entity = self.song_DAO.get_song_by_id(id)
        if song_entity is None:
            raise NoSongException("Song with that id does not exist")
        return self.song_factory.create_song_from_song_entity(song_entity)

    def create_song(self, song: CreateSong) -> ViewSong:
        #check if song with that code exists and if so raise error
        if self.song_DAO.get_song_by_code(song.code):
            raise SongWithThatCodeExists("Song with that code already exists")
        valid_authors = []
        if song.author_ids:
            for author_id in song.author_ids:
                author = self.song_DAO.get_author_by_id(author_id)
                if author:
                    valid_authors.append(author)
                else:
                    raise NoAuthorException("Author with that id does not exist")
        song_entity = self.song_factory.create_song_entity_from_song(song, valid_authors)
        song_entity = self.song_DAO.create_song(song_entity)
        return self.song_factory.create_song_from_song_entity(song_entity)

    def create_author(self, author: CreateAuthor) -> ViewAuthor:
        author_entity = self.song_factory.create_author_entity_from_author(author)
        author_entity = self.song_DAO.create_author(author_entity)
        return self.song_factory.create_author_from_author_entity(author_entity)

    def update_author(self, id, author):
        author_entity = self.song_DAO.get_author_by_id(id)
        if author_entity is None:
            raise NoAuthorException("Author with that id does not exist")
        update_values = author.dict(exclude_unset=True)
        author_entity = self.song_DAO.update_author(author_entity, update_values)
        return self.song_factory.create_author_from_author_entity(author_entity)

    def get_all_authors(self):
        author_entities = self.song_DAO.get_all_authors()
        authors = []
        for author_entity in author_entities:
            authors.append(self.song_factory.create_author_from_author_entity(author_entity))
        return authors

    def get_author_by_id(self, id):
        author_entity = self.song_DAO.get_author_by_id(id)
        if author_entity is None:
            raise NoAuthorException("Author with that id does not exist")
        return self.song_factory.create_author_from_author_entity(author_entity)

    def update_song(self, id, song):
        song_entity = self.song_DAO.get_song_by_id(id)
        if song_entity is None:
            raise NoSongException("Song with that id does not exist")
        update_values = song.dict(exclude_unset=True)

        authors_ids = update_values.pop('author_ids', song.dict())
        #validate author_ids
        valid_authors = []
        if authors_ids:
            for author_id in authors_ids:
                author = self.song_DAO.get_author_by_id(author_id)
                if author:
                    valid_authors.append(author)
                else:
                    raise NoAuthorException("Author with that id does not exist")

        if authors_ids:
            existing_author_songs = self.song_DAO.get_existing_authors_for_song(song_entity.id)
            for existing_author_song in existing_author_songs:
                self.song_DAO.delete_author_song(existing_author_song.id)

            for author in valid_authors:
                self.song_DAO.create_author_song(song_entity, author)

        song_entity = self.song_DAO.update_song(song_entity, update_values)
        return self.song_factory.create_song_from_song_entity(song_entity)
