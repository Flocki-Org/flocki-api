from fastapi import Depends

from src.app.customfields.daos.customFieldDAO import CustomFieldDAO
from src.app.customfields.models.database import models
from src.app.customfields.models.fields import (
    CreateCustomField,
    CustomFieldDefinitionView,
    CustomFieldOptionView,
    CustomFieldValueView,
    UpdateCustomField,
)
from src.app.customfields.validation import (
    FIELD_TYPES,
    SELECT_TYPES,
    CustomFieldValidationError,
    display_custom_value,
    empty_value_columns,
    normalise_custom_value,
)


class NoCustomFieldException(Exception):
    pass


class CustomFieldInUseException(Exception):
    pass


class CustomFieldService:
    def __init__(self, dao: CustomFieldDAO = Depends(CustomFieldDAO)):
        self.dao = dao

    def list_definitions(self, entity_type=None, include_inactive=False):
        return [self._definition(row) for row in self.dao.list_definitions(entity_type, include_inactive)]

    def get(self, field_id):
        row = self.dao.get(field_id)
        if row is None:
            raise NoCustomFieldException("Custom field does not exist")
        return self._definition(row)

    def create(self, payload: CreateCustomField):
        self._validate_definition(payload.field_type, payload.options, payload.default_value)
        if self.dao.get_by_name(payload.entity_type, payload.name):
            raise CustomFieldValidationError("A custom field with that name already exists for this entity")
        field = models.CustomFieldDefinition(
            name=payload.name.strip(),
            description=payload.description,
            field_type=payload.field_type,
            required=payload.required,
            active=payload.active,
            display_order=payload.display_order,
            default_value=payload.default_value,
            entity_type=payload.entity_type,
        )
        for option in payload.options:
            field.options.append(self._option(option))
        return self._definition(self.dao.add(field))

    def update(self, field_id, payload: UpdateCustomField):
        field = self.dao.get(field_id)
        if field is None:
            raise NoCustomFieldException("Custom field does not exist")
        data = payload.model_dump(exclude_unset=True)
        options = data.pop("options", None)
        field_type = data.get("field_type", field.field_type)
        if "field_type" in data or options is not None or "default_value" in data:
            option_inputs = payload.options if options is not None else [
                type("Opt", (), {"value": option.value, "label": option.label}) for option in field.options
            ]
            self._validate_definition(field_type, option_inputs, data.get("default_value", field.default_value))
        for key, value in data.items():
            setattr(field, key, value)
        if options is not None:
            field.options.clear()
            for option in payload.options:
                field.options.append(self._option(option))
        return self._definition(self.dao.save(field))

    def delete(self, field_id):
        field = self.dao.get(field_id)
        if field is None:
            raise NoCustomFieldException("Custom field does not exist")
        if self.dao.has_values(field_id):
            field.active = False
            return self._definition(self.dao.save(field))
        self.dao.delete(field)
        return None

    def values_for(self, entity_type, entity_id):
        views = []
        for row in self.dao.values_for_entity(entity_type, entity_id):
            views.append(CustomFieldValueView(
                field_id=row.field_id,
                name=row.field.name,
                field_type=row.field.field_type,
                value=display_custom_value(row.field.field_type, row),
            ))
        return views

    def set_values(self, entity_type, entity_id, items):
        for item in items:
            field = self.dao.get(item.field_id)
            if field is None or not field.active or field.entity_type != entity_type:
                raise NoCustomFieldException(f"Custom field {item.field_id} is not available for {entity_type}")
            option_values = [option.value for option in field.options if option.active]
            columns = normalise_custom_value(field.field_type, item.value, option_values, required=field.required)
            existing = self.dao.get_value(field.id, entity_type, entity_id)
            if columns == empty_value_columns():
                if existing is not None:
                    self.dao.delete_value(existing)
                continue
            if existing is None:
                existing = models.CustomFieldValue(field_id=field.id, entity_type=entity_type, entity_id=entity_id)
                self.dao.add_value(existing)
            for key, value in columns.items():
                setattr(existing, key, value)
        self.dao.db.commit()
        return self.values_for(entity_type, entity_id)

    def _validate_definition(self, field_type, options, default_value):
        if field_type not in FIELD_TYPES:
            raise CustomFieldValidationError(f"Unsupported custom field type '{field_type}'")
        option_values = [option.value for option in options] if options else []
        if field_type in SELECT_TYPES and not option_values:
            raise CustomFieldValidationError("Select fields need at least one option")
        if default_value not in (None, ""):
            normalise_custom_value(field_type, default_value, option_values, required=False)

    def _option(self, option):
        return models.CustomFieldOption(
            value=option.value,
            label=option.label or option.value,
            display_order=getattr(option, "display_order", 0) or 0,
            active=getattr(option, "active", True),
        )

    def _definition(self, row):
        options = sorted(row.options, key=lambda option: (option.display_order, option.id or 0))
        return CustomFieldDefinitionView(
            id=row.id,
            name=row.name,
            description=row.description,
            field_type=row.field_type,
            required=row.required,
            active=row.active,
            display_order=row.display_order,
            default_value=row.default_value,
            entity_type=row.entity_type,
            options=[
                CustomFieldOptionView(
                    id=option.id,
                    value=option.value,
                    label=option.label,
                    display_order=option.display_order,
                    active=option.active,
                )
                for option in options
            ],
        )
