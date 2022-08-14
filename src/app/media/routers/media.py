import uuid
from mimetypes import guess_extension

from fastapi import status, Depends, HTTPException, UploadFile
from ..services.mediaService import MediaService, NoImageException
from ..models.media import DisplayImage
from fastapi import APIRouter
from ...people.factories.peopleFactory import PeopleFactory
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['Media'])
peopleFactory = PeopleFactory()


@router.get('/media/image/{id}', response_model=DisplayImage)
def get_image_by_id(id: int, media_service: MediaService = Depends(MediaService),
                    current_user: User = Depends(get_current_user)):
    try:
        image = media_service.get_image_by_id(id)
        if image is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No image with that ID")

        return image
    except NoImageException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_message())
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

@router.post('/media/image', response_model=DisplayImage)
def upload_image(file: UploadFile, media_service: MediaService = Depends(MediaService),
                    current_user: User = Depends(get_current_user)):
    try:
        filename = file.filename + '_' + str(uuid.uuid4()) + guess_extension(
            file.content_type, strict=False).strip()
        return media_service.create_image(file, filename)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong")

