from fastapi import Depends

from .sheetFactory import SheetFactory
from ...worship.models.database import models
from ...worship.models.songs import ViewSong, CreateSong


class SongFactory:

    def __init__(self, sheet_factory: SheetFactory = Depends(SheetFactory)):
        self.sheet_factory = sheet_factory

    def create_song_entity_from_song(self, song):
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


    def create_song_from_song_entity(self, song_entity) -> ViewSong:
        if song_entity is None:
            return None

        #create list called sheets
        sheets = []
        for sheet_entity in song_entity.sheets:
            sheets.append(self.sheet_factory.create_sheet_from_sheet_entity(sheet_entity))

        return ViewSong(
            id=song_entity.id,
            code=song_entity.code,
            name=song_entity.name,
            song_key=song_entity.song_key,
            style=song_entity.style,
            tempo=song_entity.tempo,
            ccli_number=song_entity.ccli_number,
            video_link=song_entity.video_link,
            sheets=sheets)
