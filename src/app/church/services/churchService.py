#add service method to get church from DAO
from datetime import datetime

from fastapi import Depends
from starlette.responses import FileResponse

from src.app.church.daos.churchDAO import ChurchDAO
from src.app.church.factories.churchFactory import ChurchFactory
from src.app.church.models.church import CreateChurch, UpdateChurch, ViewChurch
from src.app.media.daos.mediaDAO import MediaDAO
from src.app.people.daos.addressDAO import AddressDAO


class ChurchAlreadyExists(Exception):
    pass

class NoChurchExists(Exception):
    pass


class LogoImageDoesNotExist(Exception):
    pass


class AddressDoesNotExist(Exception):
    pass


class ChurchService:
    def __init__(self, church_dao: ChurchDAO = Depends(ChurchDAO), church_factory: ChurchFactory = Depends(ChurchFactory),
                 media_DAO: MediaDAO = Depends(MediaDAO), address_DAO: AddressDAO = Depends(AddressDAO)):
        self.church_dao = church_dao
        self.church_factory = church_factory
        self.media_DAO = media_DAO
        self.address_DAO = address_DAO

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

        #validate logo image id
        if 'logo_image_id' in update_values:
            if update_values['logo_image_id'] is None:
                update_values.pop('logo_image_id')
            else:
                logo_image = self.media_DAO.get_image_by_id(update_values['logo_image_id'])
                if logo_image is None:
                    raise LogoImageDoesNotExist("Logo image does not exist")

        #validate address id
        if 'address_id' in update_values:
            if update_values['address_id'] is None:
                update_values.pop('address_id')
            else:
                address = self.address_DAO.get_address_by_id(update_values['address_id'])
                if address is None:
                    raise AddressDoesNotExist("Address does not exist")

        return self.church_factory.create_church_from_church_entity(self.church_dao.update_church(update_values))

    def delete_church(self):
        #don't allow deleting if there is no church
        if self.church_dao.get_church() is None:
            raise NoChurchExists("There is no existing church configuration to delete")
        return self.church_dao.delete_church()

    def get_church_logo(self):
        church_entity = self.church_dao.get_church()
        if church_entity is None:
            raise NoChurchExists("Church does not exist")


        if church_entity.logo_image is not None:
            logo = self.media_DAO.get_image_by_id(church_entity.logo_image.id)

            if logo is None:
                return None
            elif logo.store is not None and logo.store == 'local':
                return FileResponse(logo.address)
            elif logo.store is not None and logo.store == 's3':
                raise NotImplementedError("S3 not implemented")

            return None

        return None
