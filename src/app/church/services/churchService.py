#add service method to get church from DAO
from datetime import datetime

from fastapi import Depends

from src.app.church.daos.churchDAO import ChurchDAO
from src.app.church.factories.churchFactory import ChurchFactory
from src.app.church.models.church import CreateChurch, UpdateChurch, ViewChurch

class ChurchAlreadyExists(Exception):
    pass

class ChurchService:
    def __init__(self, church_dao: ChurchDAO = Depends(ChurchDAO), church_factory: ChurchFactory = Depends(ChurchFactory)):
        self.church_dao = church_dao
        self.church_factory = church_factory

    def get_church(self) -> ViewChurch:
        return self.church_factory.create_church_from_church_entity(self.church_dao.get_church())

    def create_church(self, church: CreateChurch):
        #don't allow more than one church in the database
        if self.church_dao.get_church() is not None:
            raise ChurchAlreadyExists("Church already exists")

        church_entity = self.church_factory.create_church_entity_from_church(church)
        church_entity.created = datetime.now()
        return self.church_factory.create_church_from_church_entity(self.church_dao.create_church(church_entity))

    def update_church(self, update_church: UpdateChurch):
        update_values = update_church.dict()
        try:
            update_values.pop('id')
        except:
            pass

        #TODO add updating of image and address.
        try:
            update_values.pop('logo_image')
        except:
            pass
        try:
            update_values.pop('address_id')
        except:
            pass
        return self.church_factory.create_church_from_church_entity(self.church_dao.update_church(update_values))



