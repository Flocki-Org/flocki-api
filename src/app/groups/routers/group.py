from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page, Params

from src.app.groups.services.groupService import (
    AddGroupMember,
    CreateGroup,
    DuplicateMembershipException,
    GroupCategoryInput,
    GroupCategoryUpdate,
    GroupCategoryView,
    GroupInUseException,
    GroupMemberView,
    GroupRoleInput,
    GroupRoleUpdate,
    GroupRoleView,
    GroupService,
    GroupView,
    NoGroupException,
    NoGroupRoleException,
    UpdateGroup,
    UpdateGroupMember,
)
from src.app.people.services.addressService import NoAddressException
from src.app.people.services.peopleService import NoPersonException
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user

router = APIRouter(tags=["Groups"])


@router.get("/groups/categories", response_model=List[GroupCategoryView])
def list_group_categories(include_inactive: bool = False, service: GroupService = Depends(GroupService),
                          current_user: User = Depends(get_current_user)):
    return service.list_categories(include_inactive)


@router.post("/groups/categories", status_code=status.HTTP_201_CREATED, response_model=GroupCategoryView)
def create_group_category(payload: GroupCategoryInput, service: GroupService = Depends(GroupService),
                          current_user: User = Depends(get_current_user)):
    try:
        return service.create_category(payload)
    except GroupInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.put("/groups/categories/{category_id}", response_model=GroupCategoryView)
def update_group_category(category_id: int, payload: GroupCategoryUpdate, service: GroupService = Depends(GroupService),
                          current_user: User = Depends(get_current_user)):
    try:
        return service.update_category(category_id, payload)
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/groups/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_category(category_id: int, service: GroupService = Depends(GroupService),
                          current_user: User = Depends(get_current_user)):
    try:
        service.delete_category(category_id)
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except GroupInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/groups/roles", response_model=List[GroupRoleView])
def list_group_roles(include_inactive: bool = False, service: GroupService = Depends(GroupService),
                     current_user: User = Depends(get_current_user)):
    return service.list_roles(include_inactive)


@router.post("/groups/roles", status_code=status.HTTP_201_CREATED, response_model=GroupRoleView)
def create_group_role(payload: GroupRoleInput, service: GroupService = Depends(GroupService),
                      current_user: User = Depends(get_current_user)):
    try:
        return service.create_role(payload)
    except GroupInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.put("/groups/roles/{role_id}", response_model=GroupRoleView)
def update_group_role(role_id: int, payload: GroupRoleUpdate, service: GroupService = Depends(GroupService),
                      current_user: User = Depends(get_current_user)):
    try:
        return service.update_role(role_id, payload)
    except NoGroupRoleException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/groups/roles/{role_id}")
def delete_group_role(role_id: int, service: GroupService = Depends(GroupService),
                      current_user: User = Depends(get_current_user)):
    try:
        role = service.delete_role(role_id)
    except NoGroupRoleException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if role is None:
        return {"deleted": True}
    return role


@router.get("/groups", response_model=Page[GroupView])
def list_groups(page: int = 1, page_size: int = 10, name: Optional[str] = None, category_id: Optional[int] = None,
                group_status: Optional[str] = Query(None, alias="status"), include_members: bool = False,
                service: GroupService = Depends(GroupService), current_user: User = Depends(get_current_user)):
    return service.search(Params(page=page, size=page_size), name, category_id, group_status, include_members)


@router.post("/groups", status_code=status.HTTP_201_CREATED, response_model=GroupView)
def create_group(payload: CreateGroup, service: GroupService = Depends(GroupService),
                 current_user: User = Depends(get_current_user)):
    try:
        return service.create(payload)
    except (NoGroupException, NoPersonException, NoAddressException) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/groups/{group_id}", response_model=GroupView)
def get_group(group_id: int, include_members: bool = False, service: GroupService = Depends(GroupService),
              current_user: User = Depends(get_current_user)):
    try:
        view = service.get(group_id, include_members=include_members)
        if not include_members:
            view.leaders = service.leaders(group_id)
        return view
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/groups/{group_id}", response_model=GroupView)
@router.patch("/groups/{group_id}", response_model=GroupView)
def update_group(group_id: int, payload: UpdateGroup, service: GroupService = Depends(GroupService),
                 current_user: User = Depends(get_current_user)):
    try:
        return service.update(group_id, payload)
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NoAddressException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/groups/{group_id}/archive", response_model=GroupView)
def archive_group(group_id: int, service: GroupService = Depends(GroupService),
                  current_user: User = Depends(get_current_user)):
    try:
        return service.archive(group_id)
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/groups/{group_id}/restore", response_model=GroupView)
def restore_group(group_id: int, service: GroupService = Depends(GroupService),
                  current_user: User = Depends(get_current_user)):
    try:
        return service.restore(group_id)
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, force: bool = False, service: GroupService = Depends(GroupService),
                 current_user: User = Depends(get_current_user)):
    try:
        service.delete(group_id, force=force)
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except GroupInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/groups/{group_id}/members", response_model=List[GroupMemberView])
def list_members(group_id: int, include_inactive: bool = False, service: GroupService = Depends(GroupService),
                 current_user: User = Depends(get_current_user)):
    try:
        return service.members(group_id, include_inactive)
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/groups/{group_id}/leaders", response_model=List[GroupMemberView])
def list_leaders(group_id: int, service: GroupService = Depends(GroupService),
                 current_user: User = Depends(get_current_user)):
    try:
        return service.leaders(group_id)
    except NoGroupException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/groups/{group_id}/members", status_code=status.HTTP_201_CREATED, response_model=GroupMemberView)
def add_member(group_id: int, payload: AddGroupMember, service: GroupService = Depends(GroupService),
               current_user: User = Depends(get_current_user)):
    try:
        return service.add_member(group_id, payload)
    except DuplicateMembershipException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except (NoGroupException, NoPersonException, NoGroupRoleException) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/groups/{group_id}/members/{person_id}", response_model=GroupMemberView)
def update_member(group_id: int, person_id: int, payload: UpdateGroupMember,
                  service: GroupService = Depends(GroupService), current_user: User = Depends(get_current_user)):
    try:
        return service.update_member(group_id, person_id, payload)
    except (NoPersonException, NoGroupRoleException) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/groups/{group_id}/members/{person_id}", response_model=GroupMemberView)
def remove_member(group_id: int, person_id: int, service: GroupService = Depends(GroupService),
                  current_user: User = Depends(get_current_user)):
    try:
        return service.remove_member(group_id, person_id)
    except NoPersonException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
