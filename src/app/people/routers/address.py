from fastapi import status, Depends, HTTPException, Response, Query
from ..services.addressService import AddressService, NoAddressException, AddressAlreadyExists, IncompleteAddress, AddressSearchUnavailable
from ...people.models.people import ViewAddress, UpdateAddress, CreateAddress
from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel
from ...users.models.user import User
from ...users.routers.login import get_current_user


class AddressSuggestion(BaseModel):
    label: str
    street_number: str = ""
    street: str = ""
    suburb: str = ""
    city: str = ""
    province: str = ""
    country: str = ""
    postal_code: str = ""
    building: Optional[str] = None
    unit: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

router = APIRouter(tags=['Address'])


@router.get('/addresses/suggest', response_model=List[AddressSuggestion])
def suggest_addresses(q: str = Query("", max_length=120), address_service: AddressService = Depends(AddressService),
                      current_user: User = Depends(get_current_user)):
    try:
        return address_service.suggest(q)
    except AddressSearchUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Address search is unavailable")


@router.get('/addresses', response_model=List[ViewAddress])
def get_addresses(address_service: AddressService = Depends(AddressService), current_user: User = Depends(get_current_user)):
    addresses_response = address_service.get_all_addresses()
    return addresses_response


@router.get('/addresses/{id}', response_model=ViewAddress)
def get_address(id: int, address_service: AddressService = Depends(AddressService),
               current_user: User = Depends(get_current_user)):
    try:
        address_response = address_service.get_by_id(id)
        if address_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with that id does not exist")

        return address_response
    except NoAddressException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with that id does not exist")

@router.put('/addresses/', response_model=ViewAddress)
def update_address(id: int, update_address: UpdateAddress, address_service: AddressService = Depends(AddressService),
                  current_user: User = Depends(get_current_user)):
    try:
        address_response = address_service.update_address(id, update_address)
        if address_response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with that id does not exist")

        return address_response
    except NoAddressException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with that id does not exist")

@router.post('/addresses', status_code=status.HTTP_201_CREATED, response_model=ViewAddress)
def add_address(address: CreateAddress, response: Response, address_service: AddressService = Depends(AddressService),
               current_user: User = Depends(get_current_user)):
    try:
        return address_service.create_address(address)
    except IncompleteAddress as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except AddressAlreadyExists as e:
        response.status_code = status.HTTP_409_CONFLICT
        return e.existing_address
