import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params

from src.app.customfields.services.customFieldService import CustomFieldService, NoCustomFieldException
from src.app.customfields.validation import CustomFieldValidationError
from src.app.departments.services.departmentService import DepartmentService
from src.app.groups.services.groupService import GroupService, NoGroupException
from src.app.people.models.contacts import (
    CategoryInput,
    CategoryUpdate,
    CategoryView,
    PersonDepartmentLink,
    PersonGroupLink,
    ReferenceValueInput,
    ReferenceValueUpdate,
    ReferenceValueView,
    RelationshipInput,
    RelationshipView,
    ServiceTypeInput,
    ServiceTypeView,
    StatusHistoryView,
)
from src.app.people.models.people import BasicViewPerson, FullViewPerson
from src.app.people.models.search import PeopleSearchFilters
from src.app.people.services.categoryService import (
    CategoryInUseException,
    CategoryService,
    NoCategoryException,
    ReferenceService,
    ServiceTypeService,
)
from src.app.people.services.peopleService import (
    DuplicateRelationshipException,
    NoPersonException,
    PeopleService,
)
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user

router = APIRouter(tags=["People"])


def _actor_id(current_user: User):
    return getattr(current_user, "id", None)


@router.get("/people/categories", response_model=List[CategoryView])
def list_categories(include_inactive: bool = False, service: CategoryService = Depends(CategoryService),
                    current_user: User = Depends(get_current_user)):
    return service.list_categories(include_inactive)


@router.post("/people/categories", status_code=status.HTTP_201_CREATED, response_model=CategoryView)
def create_category(payload: CategoryInput, service: CategoryService = Depends(CategoryService),
                    current_user: User = Depends(get_current_user)):
    try:
        return service.create(payload)
    except CategoryInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.put("/people/categories/{category_id}", response_model=CategoryView)
def update_category(category_id: int, payload: CategoryUpdate, service: CategoryService = Depends(CategoryService),
                    current_user: User = Depends(get_current_user)):
    try:
        return service.update(category_id, payload)
    except NoCategoryException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/people/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, service: CategoryService = Depends(CategoryService),
                    current_user: User = Depends(get_current_user)):
    try:
        service.delete(category_id)
    except NoCategoryException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CategoryInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/people/upcoming-birthdays", response_model=List[FullViewPerson])
def upcoming_birthdays(days: int = Query(30, ge=0, le=366), people_service: PeopleService = Depends(PeopleService),
                       current_user: User = Depends(get_current_user)):
    return people_service.report("birthdays", days)


@router.get("/people/upcoming-anniversaries", response_model=List[FullViewPerson])
def upcoming_anniversaries(days: int = Query(30, ge=0, le=366), people_service: PeopleService = Depends(PeopleService),
                           current_user: User = Depends(get_current_user)):
    return people_service.report("anniversaries", days)


@router.get("/people/without-email", response_model=List[FullViewPerson])
def without_email(people_service: PeopleService = Depends(PeopleService), current_user: User = Depends(get_current_user)):
    return people_service.report("without_email")


@router.get("/people/without-mobile", response_model=List[FullViewPerson])
def without_mobile(people_service: PeopleService = Depends(PeopleService), current_user: User = Depends(get_current_user)):
    return people_service.report("without_mobile")


@router.get("/people/without-group", response_model=List[FullViewPerson])
def without_group(people_service: PeopleService = Depends(PeopleService), current_user: User = Depends(get_current_user)):
    return people_service.report("without_group")


@router.get("/people/inactive", response_model=List[FullViewPerson])
def inactive_people(people_service: PeopleService = Depends(PeopleService), current_user: User = Depends(get_current_user)):
    return people_service.report("inactive")


@router.get("/people/with_birthday_before", name="Get people with birthdays before date")
def birthdays_before(date: datetime.date, people_service: PeopleService = Depends(PeopleService),
                     current_user: User = Depends(get_current_user)):
    return people_service.find_people_with_birthday_before_given_date(date)


@router.get("/people/with_anniversary_before", name="Get people with anniversaries before date")
def anniversaries_before(date: datetime.date, people_service: PeopleService = Depends(PeopleService),
                         current_user: User = Depends(get_current_user)):
    return people_service.find_people_with_anniversary_before_given_date(date)


@router.get("/reference-data", response_model=List[ReferenceValueView])
def list_reference_data(domain: Optional[str] = None, include_inactive: bool = False,
                        service: ReferenceService = Depends(ReferenceService),
                        current_user: User = Depends(get_current_user)):
    return service.list_values(domain, include_inactive)


@router.post("/reference-data", status_code=status.HTTP_201_CREATED, response_model=ReferenceValueView)
def create_reference_data(payload: ReferenceValueInput, service: ReferenceService = Depends(ReferenceService),
                          current_user: User = Depends(get_current_user)):
    try:
        return service.create(payload)
    except CategoryInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.put("/reference-data/{value_id}", response_model=ReferenceValueView)
def update_reference_data(value_id: int, payload: ReferenceValueUpdate,
                          service: ReferenceService = Depends(ReferenceService),
                          current_user: User = Depends(get_current_user)):
    try:
        return service.update(value_id, payload)
    except NoCategoryException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/service-types", response_model=List[ServiceTypeView])
def list_service_types(include_inactive: bool = False, service: ServiceTypeService = Depends(ServiceTypeService),
                       current_user: User = Depends(get_current_user)):
    return service.list_types(include_inactive)


@router.post("/service-types", status_code=status.HTTP_201_CREATED, response_model=ServiceTypeView)
def create_service_type(payload: ServiceTypeInput, service: ServiceTypeService = Depends(ServiceTypeService),
                        current_user: User = Depends(get_current_user)):
    return service.create(payload)


def build_people_filters(
        first_name: Optional[str] = None,
        preferred_name: Optional[str] = None,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        gender: Optional[str] = None,
        marital_status: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        date_of_birth: Optional[datetime.date] = None,
        birthday_month: Optional[int] = Query(None, ge=1, le=12),
        membership_status: Optional[str] = None,
        category_id: Optional[List[int]] = Query(None),
        household_id: Optional[int] = None,
        group_id: Optional[int] = None,
        department_id: Optional[int] = None,
        lifecycle_status: Optional[str] = None,
        archived: Optional[bool] = None,
        custom_field_id: Optional[int] = None,
        custom_field_value: Optional[str] = None,
        sort: Optional[str] = None,
        direction: str = Query("asc", pattern="^(asc|desc)$"),
) -> PeopleSearchFilters:
    return PeopleSearchFilters(
        first_name=first_name,
        preferred_name=preferred_name,
        last_name=last_name,
        full_name=full_name,
        email=email,
        phone=phone,
        gender=gender,
        marital_status=marital_status,
        age_min=age_min,
        age_max=age_max,
        date_of_birth=date_of_birth,
        birthday_month=birthday_month,
        membership_status=membership_status,
        category_ids=category_id or [],
        household_id=household_id,
        group_id=group_id,
        department_id=department_id,
        lifecycle_status=lifecycle_status,
        archived=archived,
        custom_field_id=custom_field_id,
        custom_field_value=custom_field_value,
        sort=sort,
        direction=direction,
    )
