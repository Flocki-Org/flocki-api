from datetime import datetime

from fastapi import Depends
from starlette.responses import FileResponse, StreamingResponse

from src.app.config import settings
from src.app.media.daos.mediaDAO import MediaDAO

import os.path

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.media import CreateImage
from src.app.utils.s3Utils import S3Utils


class UnsupportedImageStoreException(Exception):
    pass


class NoImageException(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.message = message

    def get_message(self):
        return self.message


class MediaService:
    def __init__(self, media_DAO: MediaDAO = Depends(MediaDAO), media_factory: MediaFactory = Depends(MediaFactory)):
        self.media_DAO = media_DAO
        self.media_factory = media_factory
        self.s3Utils = S3Utils(region = settings.flocki_s3_region_name,
                               bucket_name = settings.flocki_s3_bucket_name,
                               access_key = settings.flocki_s3_access_key,
                               secret_access_key = settings.flocki_s3_secret_access_key)

    def get_image_by_id(self, id):
        image = self.media_DAO.get_image_by_id(id)
        if image is None:
            raise NoImageException("No image with that ID")
        if image.store == 'local':
            if not os.path.isfile(image.address):
                raise NoImageException(f"No image the filename stored for the provided ID: {id}")
            return FileResponse(image.address)
        elif image.store == 's3':
            if(image is None):
                raise NoImageException(f"No image with the filename stored for the provided ID: {id}")
            #return StreamingResponse
            obj = self.s3Utils.get_file(image.filename)
            return StreamingResponse(obj['Body'], media_type=image.content_type)
        else:
            raise NotImplementedError("Image store not implemented")

    def upload_image(self, file, filename, description=None):
        print("got in upload_image methopd")
        if settings.flocki_image_store == 'local':
            os.makedirs(os.path.dirname(settings.flocki_image_base_path), exist_ok=True)
            if file.content_type == 'image/jpeg':
                file.content_type = 'image/jpg'  # TODO this is a bit of hack to make sure the extension is .jpg and not .jpe

            if not settings.flocki_image_base_path.endswith('/'):
                settings.flocki_image_base_path += '/'

            file_path = settings.flocki_image_base_path + filename
            with open(file_path, 'wb') as f:
                f.write(file.file.read())
            image = CreateImage(
                store=settings.flocki_image_store,
                address=file_path,
                created=datetime.now(),
                filename=filename,
                description=description,
                content_type=file.content_type
            )
        elif settings.flocki_image_store == 's3':
            print("got in upload_image s3 methopd")

            if self.s3Utils.upload_file(file.file, filename):
                image = CreateImage(
                    store=settings.flocki_image_store,
                    address="s3://"+settings.flocki_s3_bucket_name+"/"+filename,
                    created=datetime.now(),
                    filename=filename,
                    description=description,
                    content_type=file.content_type
                )
            else:
                raise Exception("File upload failed")

        else:
            raise UnsupportedImageStoreException("Unsupported image store: " + settings.flocki_image_store)

        image_entity = self.media_factory.create_image_entity_from_image(image)
        image_entity = self.media_DAO.add_image(image_entity)
        return image_entity

    # create image is intended to be called by the media router as it returns the image model, not the entity. Upload
    # image returns the entity and is to be called by another service (e.g. peopleService)
    def create_image(self, file, filename, description=None):
        return self.media_factory.create_image_from_image_entity(self.upload_image(file, filename, description))
