from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImportRecord(BaseModel):
    external_id: str
    model_config = ConfigDict(extra="allow")


class ImportPerson(ImportRecord):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    middle_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    date_of_birth: Optional[str] = None
    marriage_date: Optional[str] = None
    lifecycle_status: Optional[str] = None
    membership_status: Optional[str] = None


class ImportHousehold(ImportRecord):
    name: Optional[str] = None
    notes: Optional[str] = None
    leader_external_id: str
    member_external_ids: list[str] = Field(default_factory=list)
    address: Optional[dict] = None


class ImportGroup(ImportRecord):
    name: str
    description: Optional[str] = None
    category_external_id: Optional[str] = None
    status: str = "active"
    meeting_day: Optional[str] = None
    meeting_frequency: Optional[str] = None
    meeting_location: Optional[str] = None


class ImportMembership(BaseModel):
    group_external_id: str
    person_external_id: str
    role_name: Optional[str] = "Member"
    status: str = "active"
    model_config = ConfigDict(extra="allow")


class ImportCategory(ImportRecord):
    name: str
    description: Optional[str] = None
    colour: Optional[str] = None
    kind: str = "person"


class ImportCustomField(ImportRecord):
    name: str
    field_type: str
    entity_type: str = "person"
    description: Optional[str] = None
    required: bool = False
    options: list[str] = Field(default_factory=list)


class ImportCustomFieldValue(BaseModel):
    person_external_id: str
    field_external_id: str
    value: Any = None
    model_config = ConfigDict(extra="allow")


class ImportBundle(BaseModel):
    source: str = "elvanto"
    people: list[ImportPerson] = Field(default_factory=list)
    households: list[ImportHousehold] = Field(default_factory=list)
    groups: list[ImportGroup] = Field(default_factory=list)
    memberships: list[ImportMembership] = Field(default_factory=list)
    categories: list[ImportCategory] = Field(default_factory=list)
    custom_fields: list[ImportCustomField] = Field(default_factory=list)
    custom_field_values: list[ImportCustomFieldValue] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "elvanto",
                "people": [{"external_id": "p-1", "first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}],
                "groups": [{"external_id": "g-1", "name": "Bible study"}],
                "memberships": [{"group_external_id": "g-1", "person_external_id": "p-1", "role_name": "Leader"}],
            }
        }
    )
