from fastapi import Depends

from fastapi_pagination import Page, Params
from starlette.responses import FileResponse

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.services.mediaService import MediaService
from src.app.worship.daos.songDAO import SongDAO
from src.app.worship.daos.sheetDAO import SheetDAO
from src.app.worship.factories.songFactory import SongFactory
from src.app.worship.models.database.models import Sheet
from src.app.worship.factories.sheetFactory import SheetFactory
from src.app.worship.models.songs import ViewSheet, CreateSheet, SheetType


class NoSongException (Exception):
    pass


class SheetService:
    def __init__(self, sheet_factory: SheetFactory = Depends(SheetFactory), sheet_DAO: SheetDAO = Depends(SheetDAO),
                 song_DAO: SongDAO = Depends(SongDAO), media_service: MediaService = Depends(MediaService),
                 media_factory: MediaFactory = Depends(MediaFactory), song_factory: SongFactory = Depends(SongFactory)):
        self.sheet_factory = sheet_factory
        self.sheet_DAO = sheet_DAO
        self.song_factory = song_factory
        self.song_DAO = song_DAO
        self.media_service = media_service
        self.media_factory = media_factory

    def upload_song_sheet(self, song_id, type, sheet_key, file):
        song_entity = self.song_DAO.get_song_by_id(song_id)
        if song_entity is None:
            raise NoSongException("Song with that id does not exist")

        if file.content_type != "application/pdf":
            raise ValueError("Only PDF files are allowed")
        #create name as song_entity.code_type_sheet_key.pdf
        filename = f"{song_entity.code}_{type}_{sheet_key}.pdf"
        uploaded_media_item = self.media_service.upload_media_item(file, filename, "application/pdf")
        sheet_entity = self.sheet_factory.create_sheet_entity_from_details(
            song_entity, type, sheet_key, uploaded_media_item.id)
        self.sheet_DAO.create_sheet(sheet_entity)

        song_entity = self.song_DAO.get_song_by_id(song_id)
        return self.song_factory.create_song_from_song_entity(song_entity)

    def get_song_sheet(self, song_id, type, sheet_key):
        song_entity = self.song_DAO.get_song_by_id(song_id)
        if song_entity is None:
            raise NoSongException("Song with that id does not exist")

        if sheet_key is None:
            sheet_key = song_entity.song_key

        sheet_entity = self.sheet_DAO.get_song_sheet(song_id, type, sheet_key)
        if sheet_entity is None:
            raise NoSongException("Sheet with that id does not exist")

        return self.media_service.get_media_item_by_id(sheet_entity.media_item_id, as_attachment=False)

    def get_sheet_types(self):
        return [type.value for type in SheetType]

    def update_song_sheet(self, song_id, type, sheet_key, file):
        song_entity = self.song_DAO.get_song_by_id(song_id)
        if song_entity is None:
            raise NoSongException("Song with that id does not exist")

        if file.content_type != "application/pdf":
            raise ValueError("Only PDF files are allowed")

        #create name as song_entity.code_type_sheet_key.pdf
        filename = f"{song_entity.code}_{type}_{sheet_key}.pdf"
        uploaded_media_item = self.media_service.upload_media_item(file, filename, "application/pdf")
        sheet_entity = self.sheet_DAO.get_song_sheet(song_id, type, sheet_key)
        if sheet_entity is None:
            raise NoSongException("Sheet with that id does not exist")
        sheet_entity.media_item_id = uploaded_media_item.id
        self.sheet_DAO.update_sheet(sheet_entity)
        song_entity = self.song_DAO.get_song_by_id(song_id)
        return self.song_factory.create_song_from_song_entity(song_entity)
