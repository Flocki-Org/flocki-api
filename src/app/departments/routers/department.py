from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.departments.services.departmentService import (
    DepartmentCycleException,
    DepartmentGroupInput,
    DepartmentInUseException,
    DepartmentInput,
    DepartmentPersonInput,
    DepartmentService,
    DepartmentUpdate,
    DepartmentView,
    NoDepartmentException,
)
from src.app.people.services.peopleService import NoPersonException
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user

router = APIRouter(tags=["Departments"])


@router.get("/departments", response_model=List[DepartmentView])
def list_departments(include_inactive: bool = False, service: DepartmentService = Depends(DepartmentService),
                     current_user: User = Depends(get_current_user)):
    return service.list_departments(include_inactive)


@router.post("/departments", status_code=status.HTTP_201_CREATED, response_model=DepartmentView)
def create_department(payload: DepartmentInput, service: DepartmentService = Depends(DepartmentService),
                      current_user: User = Depends(get_current_user)):
    try:
        return service.create(payload)
    except (NoDepartmentException, DepartmentCycleException) as exc:
        code = status.HTTP_400_BAD_REQUEST if isinstance(exc, DepartmentCycleException) else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=str(exc))


@router.get("/departments/{department_id}", response_model=DepartmentView)
def get_department(department_id: int, service: DepartmentService = Depends(DepartmentService),
                   current_user: User = Depends(get_current_user)):
    try:
        return service.get(department_id)
    except NoDepartmentException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/departments/{department_id}", response_model=DepartmentView)
def update_department(department_id: int, payload: DepartmentUpdate, service: DepartmentService = Depends(DepartmentService),
                      current_user: User = Depends(get_current_user)):
    try:
        return service.update(department_id, payload)
    except NoDepartmentException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DepartmentCycleException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: int, service: DepartmentService = Depends(DepartmentService),
                      current_user: User = Depends(get_current_user)):
    try:
        service.delete(department_id)
    except NoDepartmentException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DepartmentInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/departments/{department_id}/people", response_model=DepartmentView)
def add_department_person(department_id: int, payload: DepartmentPersonInput,
                          service: DepartmentService = Depends(DepartmentService),
                          current_user: User = Depends(get_current_user)):
    try:
        return service.add_person(department_id, payload)
    except NoPersonException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DepartmentInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except NoDepartmentException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/departments/{department_id}/people/{person_id}", response_model=DepartmentView)
def remove_department_person(department_id: int, person_id: int, service: DepartmentService = Depends(DepartmentService),
                             current_user: User = Depends(get_current_user)):
    try:
        return service.remove_person(department_id, person_id)
    except (NoPersonException, NoDepartmentException) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/departments/{department_id}/groups", response_model=DepartmentView)
def add_department_group(department_id: int, payload: DepartmentGroupInput,
                         service: DepartmentService = Depends(DepartmentService),
                         current_user: User = Depends(get_current_user)):
    try:
        return service.add_group(department_id, payload)
    except DepartmentInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except NoDepartmentException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/departments/{department_id}/groups/{group_id}", response_model=DepartmentView)
def remove_department_group(department_id: int, group_id: int, service: DepartmentService = Depends(DepartmentService),
                            current_user: User = Depends(get_current_user)):
    try:
        return service.remove_group(department_id, group_id)
    except NoDepartmentException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
