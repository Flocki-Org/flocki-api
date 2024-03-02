from fastapi import Depends

from fastapi_pagination import Page, Params

from src.app.worship.daos.songDAO import SongDAO
from src.app.worship.models.database.models import Song
from src.app.worship.factories.songFactory import SongFactory
from src.app.worship.models.songs import ViewSong, CreateArtist, ViewArtist, CreateSong


class NoSongException (Exception):
    pass


class SongWithThatCodeExists (Exception):
    pass


class NoArtistException(Exception):
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
        song_entity = self.song_factory.create_song_entity_from_song(song)
        song_entity = self.song_DAO.create_song(song_entity)
        return self.song_factory.create_song_from_song_entity(song_entity)

    def create_artist(self, artist: CreateArtist) -> ViewArtist:
        artist_entity = self.song_factory.create_artist_entity_from_artist(artist)
        artist_entity = self.song_DAO.create_artist(artist_entity)
        return self.song_factory.create_artist_from_artist_entity(artist_entity)

    def update_artist(self, id, artist):
        artist_entity = self.song_DAO.get_artist_by_id(id)
        if artist_entity is None:
            raise NoArtistException("Artist with that id does not exist")
        update_values = artist.dict(exclude_unset=True)
        artist_entity = self.song_DAO.update_artist(artist_entity, update_values)
        return self.song_factory.create_artist_from_artist_entity(artist_entity)

    def get_all_artists(self):
        artist_entities = self.song_DAO.get_all_artists()
        artists = []
        for artist_entity in artist_entities:
            artists.append(self.song_factory.create_artist_from_artist_entity(artist_entity))
        return artists

    def get_artist_by_id(self, id):
        artist_entity = self.song_DAO.get_artist_by_id(id)
        if artist_entity is None:
            raise NoArtistException("Artist with that id does not exist")
        return self.song_factory.create_artist_from_artist_entity(artist_entity)

    def update_song(self, id, song):
        song_entity = self.song_DAO.get_song_by_id(id)
        if song_entity is None:
            raise NoSongException("Song with that id does not exist")
        update_values = song.dict(exclude_unset=True)
        song_entity = self.song_DAO.update_song(song_entity, update_values)
        return self.song_factory.create_song_from_song_entity(song_entity)
