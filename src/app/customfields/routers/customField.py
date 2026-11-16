from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.app.customfields.models.fields import (
    CreateCustomField,
    CustomFieldDefinitionView,
    CustomFieldValueInput,
    CustomFieldValueView,
    UpdateCustomField,
)
from src.app.customfields.services.customFieldService import CustomFieldService, NoCustomFieldException
from src.app.customfields.validation import CustomFieldValidationError
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user

router = APIRouter(tags=["Custom fields"])


@router.get("/custom-fields", response_model=List[CustomFieldDefinitionView])
def list_custom_fields(entity_type: Optional[str] = None, include_inactive: bool = False,
                       service: CustomFieldService = Depends(CustomFieldService),
                       current_user: User = Depends(get_current_user)):
    return service.list_definitions(entity_type, include_inactive)


@router.post("/custom-fields", status_code=status.HTTP_201_CREATED, response_model=CustomFieldDefinitionView)
def create_custom_field(payload: CreateCustomField, service: CustomFieldService = Depends(CustomFieldService),
                        current_user: User = Depends(get_current_user)):
    try:
        return service.create(payload)
    except CustomFieldValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/custom-fields/{field_id}", response_model=CustomFieldDefinitionView)
def update_custom_field(field_id: int, payload: UpdateCustomField, service: CustomFieldService = Depends(CustomFieldService),
                        current_user: User = Depends(get_current_user)):
    try:
        return service.update(field_id, payload)
    except NoCustomFieldException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CustomFieldValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/custom-fields/{field_id}")
def delete_custom_field(field_id: int, service: CustomFieldService = Depends(CustomFieldService),
                        current_user: User = Depends(get_current_user)):
    try:
        field = service.delete(field_id)
    except NoCustomFieldException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if field is None:
        return {"deleted": True}
    return field


@router.get("/people/{person_id}/custom-fields", response_model=List[CustomFieldValueView])
def get_person_custom_fields(person_id: int, service: CustomFieldService = Depends(CustomFieldService),
                             current_user: User = Depends(get_current_user)):
    return service.values_for("person", person_id)


@router.put("/people/{person_id}/custom-fields", response_model=List[CustomFieldValueView])
def set_person_custom_fields(person_id: int, values: List[CustomFieldValueInput],
                             service: CustomFieldService = Depends(CustomFieldService),
                             current_user: User = Depends(get_current_user)):
    try:
        return service.set_values("person", person_id, values)
    except NoCustomFieldException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CustomFieldValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
