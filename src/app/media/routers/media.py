import logging
import os
import uuid

from starlette.responses import FileResponse

from src.app.utils.fileUtils import FileUtils
from fastapi import status, Depends, HTTPException, UploadFile
from ..services.mediaService import MediaService, NoMediaItemException
from ..models.media import ViewMediaItem
from fastapi import APIRouter
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['Media'])


@router.get('/media/item/{id}')
def get_media_item_by_id(id: int, media_service: MediaService = Depends(MediaService)):
    try:
        media_item = media_service.get_media_item_by_id(id)
        if media_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No media_item with that ID")
        return media_item
    except NoMediaItemException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_message())
    except Exception as e:
        print(e)
        logging.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

@router.post('/media/item', response_model=ViewMediaItem)
def upload_image(file: UploadFile, media_service: MediaService = Depends(MediaService),
                    current_user: User = Depends(get_current_user)):
    try:
        #remove file extension
        filename = os.path.splitext(file.filename)[0]
        filename = (filename.strip() + '_' + str(uuid.uuid4()) + '.' + FileUtils.get_file_extension(file)).strip()
        return media_service.create_media_item(file, filename)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")


