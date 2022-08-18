from fastapi import status, Depends, HTTPException, Response
from ..services.addressService import AddressService, NoAddressException, AddressAlreadyExists
from ...people.models.people import ViewAddress, UpdateAddress, CreateAddress
from fastapi import APIRouter
from typing import List
from ...users.models.user import User
from ...users.routers.login import get_current_user

router = APIRouter(tags=['Address'])


@router.get('/addresses', response_model=List[ViewAddress])
def get_addresses(address_service: AddressService = Depends(AddressService), current_user: User = Depends(get_current_user)):
    addresses_response = address_service.get_all_addresses()
    return addresses_response


@router.get('/address/{id}', response_model=ViewAddress)
def get_address(id: int, address_service: AddressService = Depends(AddressService),
               current_user: User = Depends(get_current_user)):
    try:
        address_response = address_service.get_by_id(id)
        if address_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with that id does not exist")

        return address_response
    except NoAddressException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with that id does not exist")

@router.put('/address/', response_model=ViewAddress)
def update_address(id: int, update_address: UpdateAddress, address_service: AddressService = Depends(AddressService),
                  current_user: User = Depends(get_current_user)):
    try:
        address_response = address_service.update_address(id, update_address)
        if address_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with that id does not exist")

        return address_response
    except NoAddressException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with that id does not exist")

@router.post('/address', status_code=status.HTTP_201_CREATED, response_model=ViewAddress)
def add_address(address: CreateAddress, response: Response, address_service: AddressService = Depends(AddressService),
               current_user: User = Depends(get_current_user)):
    try:
        return address_service.create_address(address)
    except AddressAlreadyExists as e:
        response.status_code = status.HTTP_409_CONFLICT
        return e.existing_address
