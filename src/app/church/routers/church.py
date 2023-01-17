from fastapi import status, Depends, HTTPException, UploadFile, APIRouter

from src.app.church.models.church import ViewChurch, CreateChurch, UpdateChurch
from src.app.church.services.churchService import ChurchService, ChurchAlreadyExists, NoChurchExists, \
    LogoImageDoesNotExist, AddressDoesNotExist
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user

router = APIRouter(tags=['Church'])

@router.get('/church', response_model=ViewChurch)
def get_church(church_service: ChurchService = Depends(ChurchService), current_user: User = Depends(get_current_user)):
    church = church_service.get_church()
    if church is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The church has not yet been defined")
    return church

@router.post('/church', status_code=status.HTTP_201_CREATED)
def create_church(church: CreateChurch, church_service: ChurchService = Depends(ChurchService), current_user: User = Depends(get_current_user)):
    try:
        return church_service.create_church(church)
    except ChurchAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Church has already been defined. You can only update the existing record.")

@router.put('/church', status_code=status.HTTP_200_OK)
def update_church(church: UpdateChurch, church_service: ChurchService = Depends(ChurchService), current_user: User = Depends(get_current_user)):
    try:
        return church_service.update_church(church)
    except LogoImageDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The logo image does not exist")
    except AddressDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The address does not exist")
    except NoChurchExists as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The church has not yet been defined")

@router.delete('/church', status_code=status.HTTP_200_OK)
def delete_church(church_service: ChurchService = Depends(ChurchService), current_user: User = Depends(get_current_user)):
    try:
        return church_service.delete_church()
    except NoChurchExists as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is not church configuration to delete")

@router.get('/church/logo')
def get_church_logo(church_service: ChurchService = Depends(ChurchService), current_user: User = Depends(get_current_user)):
    logo_image = church_service.get_church_logo()
    if logo_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Church logo has not been defined")
    logo_image.headers['cache-control'] = 'max-age=20'
    return logo_image