from fastapi import Depends

from src.app.people.daos.categoryDAO import CategoryDAO, ReferenceDAO, ServiceTypeDAO
from src.app.people.models.contacts import (
    CategoryInput,
    CategoryUpdate,
    CategoryView,
    ReferenceValueInput,
    ReferenceValueUpdate,
    ReferenceValueView,
    ServiceTypeInput,
    ServiceTypeView,
)
from src.app.people.models.database import models


class NoCategoryException(Exception):
    pass


class CategoryInUseException(Exception):
    pass


class CategoryService:
    def __init__(self, category_dao: CategoryDAO = Depends(CategoryDAO)):
        self.category_dao = category_dao

    def list_categories(self, include_inactive=False):
        return [self._view(row) for row in self.category_dao.list_categories(include_inactive)]

    def create(self, payload: CategoryInput):
        if self.category_dao.get_by_name(payload.name):
            raise CategoryInUseException("A people category with that name already exists")
        category = models.PeopleCategory(
            name=payload.name.strip(),
            description=payload.description,
            colour=payload.colour,
            active=payload.active,
        )
        return self._view(self.category_dao.add(category))

    def update(self, category_id, payload: CategoryUpdate):
        category = self._require(category_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        return self._view(self.category_dao.save(category))

    def delete(self, category_id):
        category = self._require(category_id)
        if self.category_dao.in_use(category_id):
            raise CategoryInUseException("Remove people from this category, or deactivate it")
        self.category_dao.delete(category)

    def _require(self, category_id):
        category = self.category_dao.get(category_id)
        if category is None:
            raise NoCategoryException("People category does not exist")
        return category

    def _view(self, category):
        return CategoryView(
            id=category.id,
            name=category.name,
            description=category.description,
            colour=category.colour,
            active=bool(category.active),
        )


class ReferenceService:
    def __init__(self, reference_dao: ReferenceDAO = Depends(ReferenceDAO)):
        self.reference_dao = reference_dao

    def list_values(self, domain=None, include_inactive=False):
        return [self._view(row) for row in self.reference_dao.list_values(domain, include_inactive)]

    def create(self, payload: ReferenceValueInput):
        if self.reference_dao.get_by_domain_value(payload.domain, payload.value):
            raise CategoryInUseException("That reference value already exists")
        row = models.ReferenceValue(
            domain=payload.domain.strip(),
            value=payload.value.strip(),
            label=(payload.label or payload.value).strip(),
            description=payload.description,
            active=payload.active,
            display_order=payload.display_order,
        )
        return self._view(self.reference_dao.add(row))

    def update(self, value_id, payload: ReferenceValueUpdate):
        row = self.reference_dao.get(value_id)
        if row is None:
            raise NoCategoryException("Reference value does not exist")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        return self._view(self.reference_dao.save(row))

    def _view(self, row):
        return ReferenceValueView(
            id=row.id,
            domain=row.domain,
            value=row.value,
            label=row.label,
            description=row.description,
            active=row.active,
            display_order=row.display_order,
        )


class ServiceTypeService:
    def __init__(self, service_type_dao: ServiceTypeDAO = Depends(ServiceTypeDAO)):
        self.service_type_dao = service_type_dao

    def list_types(self, include_inactive=False):
        return [self._view(row) for row in self.service_type_dao.list_types(include_inactive)]

    def create(self, payload: ServiceTypeInput):
        row = models.ServiceType(name=payload.name.strip(), description=payload.description, active=payload.active)
        return self._view(self.service_type_dao.add(row))

    def _view(self, row):
        return ServiceTypeView(id=row.id, name=row.name, description=row.description, active=row.active)
