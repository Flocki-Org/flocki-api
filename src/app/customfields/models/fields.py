from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomFieldOptionInput(BaseModel):
    value: str
    label: Optional[str] = None
    display_order: int = 0
    active: bool = True


class CustomFieldOptionView(CustomFieldOptionInput):
    id: int


class CreateCustomField(BaseModel):
    name: str
    description: Optional[str] = None
    field_type: str
    required: bool = False
    active: bool = True
    display_order: int = 0
    default_value: Optional[str] = None
    entity_type: str = "person"
    options: List[CustomFieldOptionInput] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Shirt size",
                "description": "Used for retreat planning",
                "field_type": "single_select",
                "entity_type": "person",
                "options": [
                    {"value": "S", "label": "Small"},
                    {"value": "M", "label": "Medium"},
                    {"value": "L", "label": "Large"},
                ],
            }
        }
    )


class UpdateCustomField(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    field_type: Optional[str] = None
    required: Optional[bool] = None
    active: Optional[bool] = None
    display_order: Optional[int] = None
    default_value: Optional[str] = None
    entity_type: Optional[str] = None
    options: Optional[List[CustomFieldOptionInput]] = None


class CustomFieldDefinitionView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    field_type: str
    required: bool = False
    active: bool = True
    display_order: int = 0
    default_value: Optional[str] = None
    entity_type: str
    options: List[CustomFieldOptionView] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CustomFieldValueInput(BaseModel):
    field_id: int
    value: Any = None


class CustomFieldValueView(BaseModel):
    field_id: int
    name: str
    field_type: str
    value: Any = None
