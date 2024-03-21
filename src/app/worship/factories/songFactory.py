from typing import List

from fastapi import Depends

from .sheetFactory import SheetFactory
from ...worship.models.database import models
from ...worship.models.songs import ViewSong, CreateSong, CreateAuthor, ViewAuthor


class SongFactory:

    def __init__(self, sheet_factory: SheetFactory = Depends(SheetFactory)):
        self.sheet_factory = sheet_factory

    def create_song_entity_from_song(self, song: CreateSong, author_entities: List[models.Author]) -> models.Song:
        song_entity = models.Song(
                name=song.name,
                code=song.code,
                song_key=song.song_key,
                secondary_name=song.secondary_name,
                style=song.style,
                tempo=song.tempo,
                ccli_number=song.ccli_number,
                video_link=song.video_link)

        if(author_entities):
            for author_entity in author_entities:
                song_entity.authors.append(models.AuthorSong(author=author_entity))

        return song_entity


    def create_song_from_song_entity(self, song_entity: models.Song) -> ViewSong:
        if song_entity is None:
            raise ValueError("Song entity cannot be None")

        #create list called sheets
        sheets = []
        for sheet_entity in song_entity.sheets:
            sheets.append(self.sheet_factory.create_sheet_from_sheet_entity(sheet_entity))

        view_authors = []
        for author_song in song_entity.authors:
            view_authors.append(self.create_author_from_author_entity(author_song.author))

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
            authors=view_authors)

    def create_author_entity_from_author(self, author: CreateAuthor):
        if author is None:
            raise ValueError("Author cannot be None")

        return models.Author(name=author.name)

    def create_author_from_author_entity(self, author_entity):
        if author_entity is None:
            raise ValueError("Author entity cannot be None")

        return ViewAuthor(
            id=author_entity.id,
            name=author_entity.name)
