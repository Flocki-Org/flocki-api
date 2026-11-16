from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from src.app.imports.models.bundle import ImportBundle
from src.app.imports.services.importService import ImportService
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user

router = APIRouter(tags=["Imports"])


@router.post("/imports/elvanto")
def import_elvanto(bundle: ImportBundle, service: ImportService = Depends(ImportService),
                   current_user: User = Depends(get_current_user)):
    """Import people, households, groups, categories and custom fields.

    The same external ids can be submitted again. Existing rows are updated and
    unknown source fields are stored with the external reference.
    """
    return service.import_bundle(bundle)


@router.get("/imports/errors")
def import_errors(source: Optional[str] = None, service: ImportService = Depends(ImportService),
                  current_user: User = Depends(get_current_user)):
    return service.errors(source)
