import io
from datetime import datetime

from fastapi import Depends
from starlette.responses import FileResponse, StreamingResponse

from src.app.config import settings
from src.app.media.daos.mediaDAO import MediaDAO

import os.path

from src.app.media.factories.mediaFactory import MediaFactory
from src.app.media.models.database import models
from src.app.media.models.media import CreateMediaItem
from src.app.utils.s3Utils import S3Utils


class UnsupportedMediaItemStoreException(Exception):
    pass


class NoMediaItemException(Exception):
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

    def get_media_item_by_id(self, id, as_attachment=True):
        media_item = self.media_DAO.get_media_item_by_id(id)
        if media_item is None:
            raise NoMediaItemException("No media item with that ID")
        if media_item.store == 'local':
            if not os.path.isfile(media_item.address):
                raise NoMediaItemException(f"No media item the filename stored for the provided ID: {id}")
            file_rsp = FileResponse(media_item.address, media_type=media_item.content_type, filename=media_item.filename)
            if as_attachment:
                file_rsp.headers['Content-Disposition'] = f'attachment; filename="{media_item.filename}"'
            else:
                file_rsp.headers['Content-Disposition'] = f'inline; filename="{media_item.filename}"'
            return file_rsp
        elif media_item.store == 's3':
            if(media_item is None):
                raise NoMediaItemException(f"No media item with the filename stored for the provided ID: {id}")
            #return StreamingResponse
            obj = self.s3Utils.get_file(media_item.filename)
            #response = FileResponse(None, filename=media_item.filename, media_type=media_item.content_type, content_disposition_type="attachment")
            #file_obj = io.BytesIO(obj['Body'].read())

            # Get the content type of the object
            content_type = media_item.content_type

            # Set the Content-Disposition header to force download with the original filename
            if 'Key' in obj:
                filename = obj['Key']
            else:
                filename = media_item.filename

            headers = {
                "Content-Disposition": f"attachment; filename={filename}"
            }
            streaming_rsp = StreamingResponse(obj['Body'].iter_chunks(), media_type=content_type, headers=headers)
            return streaming_rsp
        else:
            raise NotImplementedError("Media Item store not implemented")

    def upload_media_item(self, file, filename, description=None) -> models.MediaItem:
        file.file.seek(0)
        if settings.flocki_media_store == 'local':
            os.makedirs(os.path.dirname(settings.flocki_media_base_path), exist_ok=True)

            if not settings.flocki_media_base_path.endswith('/'):
                settings.flocki_media_base_path += '/'

            file_path = settings.flocki_media_base_path + filename
            with open(file_path, 'wb') as f:
                f.write(file.file.read())

            media_item = CreateMediaItem(
                store=settings.flocki_media_store,
                address=file_path,
                created=datetime.now(),
                filename=filename,
                description=description,
                content_type=file.content_type)

        elif settings.flocki_media_store == 's3':
            if self.s3Utils.upload_file(file.file, filename):
                media_item = CreateMediaItem(
                    store=settings.flocki_media_store,
                    address="s3://"+settings.flocki_s3_bucket_name+"/"+filename,
                    created=datetime.now(),
                    filename=filename,
                    description=description,
                    content_type=file.content_type
                )
            else:
                raise Exception("File upload failed")

        else:
            raise UnsupportedMediaItemStoreException("Unsupported media item store: " + settings.flocki_media_store)

        media_item_entity = self.media_factory.create_media_item_entity_from_media_item(media_item)
        media_item_entity = self.media_DAO.add_media_item(media_item_entity)
        return media_item_entity

    # create media item is intended to be called by the media routers as it returns the media item model, not the entity. Upload
    # media item returns the entity and is to be called by another service
    def create_media_item(self, file, filename, description=None):
        return self.media_factory.create_media_item_from_media_item_entity(self.upload_media_item(file, filename, description))

    def upload_image(self, file, filename, description):
        # TODO this is a bit of hack to make sure the extension is .jpg and not .jpeg
        if file.content_type == 'image/jpeg':
            file.content_type = 'image/jpg'
        return self.upload_media_item(file, filename, description)

