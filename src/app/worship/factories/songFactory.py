from fastapi import Depends

from .sheetFactory import SheetFactory
from ...worship.models.database import models
from ...worship.models.songs import ViewSong, CreateSong, CreateArtist, ViewArtist


class SongFactory:

    def __init__(self, sheet_factory: SheetFactory = Depends(SheetFactory)):
        self.sheet_factory = sheet_factory

    def create_song_entity_from_song(self, song: CreateSong) -> models.Song:
        song_entity = models.Song(
                name=song.name,
                code=song.code,
                song_key=song.song_key,
                secondary_name=song.secondary_name,
                artist_id=song.artist_id,
                style=song.style,
                tempo=song.tempo,
                ccli_number=song.ccli_number,
                video_link=song.video_link)
        return song_entity


    def create_song_from_song_entity(self, song_entity: models.Song) -> ViewSong:
        if song_entity is None:
            raise ValueError("Song entity cannot be None")

        #create list called sheets
        sheets = []
        for sheet_entity in song_entity.sheets:
            sheets.append(self.sheet_factory.create_sheet_from_sheet_entity(sheet_entity))

        view_artist = self.create_artist_from_artist_entity(song_entity.artist)

        return ViewSong(
            id=song_entity.id,
            code=song_entity.code,
            name=song_entity.name,
            song_key=song_entity.song_key,
            style=song_entity.style,
            tempo=song_entity.tempo,
            ccli_number=song_entity.ccli_number,
            video_link=song_entity.video_link,
            sheets=sheets,
            artist=view_artist)

    def create_artist_entity_from_artist(self, artist: CreateArtist):
        if artist is None:
            raise ValueError("Artist cannot be None")

        return models.Artist(name=artist.name)

    def create_artist_from_artist_entity(self, artist_entity):
        if artist_entity is None:
            raise ValueError("Artist entity cannot be None")

        return ViewArtist(
            id=artist_entity.id,
            name=artist_entity.name)
