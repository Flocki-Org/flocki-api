import logging
import os
import uuid
from src.app.utils.fileUtils import FileUtils
from fastapi import status, Depends, HTTPException, UploadFile
from ...media.services.mediaService import MediaService, NoMediaItemException
from ...media.models.media import ViewMediaItem
from fastapi import APIRouter
from ...people.factories.peopleFactory import PeopleFactory
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['Images'])
peopleFactory = PeopleFactory()

@router.get('/images/{id}')
def get_image_by_id(id: int, media_service: MediaService = Depends(MediaService)):
    try:
        image = media_service.get_media_item_by_id(id, as_attachment=False)

        if image is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No image with that ID")

        image.headers['cache-control'] = 'max-age=20'

        return image
    except NoMediaItemException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_message())
    except Exception as e:
        print(e)
        logging.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

@router.post('/image', response_model=ViewMediaItem)
def upload_image(file: UploadFile, media_service: MediaService = Depends(MediaService),
                    current_user: User = Depends(get_current_user)):
    try:
        #remove file extension
        filename = os.path.splitext(file.filename)[0]
        filename = (filename.strip() + '_' + str(uuid.uuid4()) + '.' + FileUtils.get_file_extension(file)).strip()
        return media_service.create_media_item(file, filename)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


