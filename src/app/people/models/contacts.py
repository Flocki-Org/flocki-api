from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PersonEmailInput(BaseModel):
    email: EmailStr
    is_primary: bool = False
    label: Optional[str] = None


class PersonEmailView(PersonEmailInput):
    id: Optional[int] = None


class PersonPhoneInput(BaseModel):
    number: str
    phone_type: str = "mobile"
    is_primary: bool = False
    label: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"number": "+27721234567", "phone_type": "mobile", "is_primary": True}
        }
    )


class PersonPhoneView(PersonPhoneInput):
    id: Optional[int] = None


class EmergencyContactInput(BaseModel):
    name: str
    relationship_label: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class EmergencyContactView(EmergencyContactInput):
    id: Optional[int] = None


class CategoryInput(BaseModel):
    name: str
    description: Optional[str] = None
    colour: Optional[str] = None
    active: bool = True

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Volunteers", "description": "People who serve", "colour": "#2F6FED"}}
    )


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    colour: Optional[str] = None
    active: Optional[bool] = None


class CategoryView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    colour: Optional[str] = None
    active: bool = True

    model_config = ConfigDict(from_attributes=True)


class RelationshipInput(BaseModel):
    related_person_id: int
    relationship_type: str = Field(description="spouse, parent, child, sibling, guardian, dependent, or other")
    notes: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={"example": {"related_person_id": 4, "relationship_type": "spouse"}}
    )


class RelationshipView(BaseModel):
    id: int
    person_id: int
    related_person_id: int
    relationship_type: str
    direction: str
    notes: Optional[str] = None
    related_first_name: Optional[str] = None
    related_last_name: Optional[str] = None


class ServiceTypeInput(BaseModel):
    name: str
    description: Optional[str] = None
    active: bool = True


class ServiceTypeView(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ReferenceValueInput(BaseModel):
    domain: str
    value: str
    label: Optional[str] = None
    description: Optional[str] = None
    active: bool = True
    display_order: int = 0


class ReferenceValueUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    display_order: Optional[int] = None


class ReferenceValueView(BaseModel):
    id: int
    domain: str
    value: str
    label: str
    description: Optional[str] = None
    active: bool = True
    display_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class StatusHistoryView(BaseModel):
    id: int
    field_name: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None
    changed_at: Optional[str] = None
    changed_by_user_id: Optional[int] = None


class PersonGroupLink(BaseModel):
    group_id: int
    group_name: str
    role: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None


class PersonDepartmentLink(BaseModel):
    department_id: int
    name: str
    parent_id: Optional[int] = None
