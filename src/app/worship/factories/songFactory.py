from fastapi import Depends

from ...worship.models.database import models
from ...worship.models.songs import ViewSong, CreateSong


class SongFactory:

    def __init__(self):
        pass

    def create_song_entity_from_song(self, song):
        song_entity = models.Song(
                name=song.name,
                description=song.description,
                lyrics=song.lyrics,
                artist_id=song.artist_id,
                style=song.style,
                tempo=song.tempo,
                ccli_number=song.ccli_number,
                video_link=song.video_link)
        return song_entity


    def create_song_from_song_entity(self, song_entity) -> ViewSong:
        if song_entity is None:
            return None

        return ViewSong(
            id=song_entity.id,
            name=song_entity.name,
            song_key=song_entity.song_key,
            style=song_entity.style,
            tempo=song_entity.tempo,
            ccli_number=song_entity.ccli_number,
            video_link=song_entity.video_link)
