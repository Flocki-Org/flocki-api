from __future__ import annotations

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, field_validator, model_validator
import datetime
from enum import Enum
from typing import Annotated, List, ForwardRef, Optional

def _coerce_date(value):
    # Pydantic v1 turned a datetime into its date. v2 rejects a datetime that has a time.
    if isinstance(value, datetime.datetime):
        return value.date()
    return value

CoercedDate = Annotated[datetime.date, BeforeValidator(_coerce_date)]

# from src.app.people.models.household import Household
from src.app.customfields.models.fields import CustomFieldValueInput, CustomFieldValueView
from src.app.media.models.media import CreateMediaItem, ViewMediaItem
from src.app.people.models.contacts import (
    CategoryView,
    EmergencyContactInput,
    EmergencyContactView,
    PersonDepartmentLink,
    PersonEmailInput,
    PersonEmailView,
    PersonGroupLink,
    PersonPhoneInput,
    PersonPhoneView,
    RelationshipView,
    ServiceTypeView,
)
from src.app.users.models.user import DisplayUser
from src.app.utils.httpUrl import HttpUrl

Household = ForwardRef('Household')
FullViewPerson = ForwardRef('FullViewPerson')

class Gender(str, Enum):
    male = 'male'
    female = 'female'


class MaritalStatus(str, Enum):
    single = 'single'
    married = 'married'
    divorced = 'divorced'
    remarried = 'remarried'


class SocialMediaType(str, Enum):
    linkedin = 'linkedin'
    facebook = 'facebook'
    twitter = 'twitter'
    instagram = 'instagram'
    tiktok = 'tiktok'


class AddressType(str, Enum):
    home = 'home'
    postal = 'postal'
    business = 'business'
    student_accommodation = 'student_accommodation'
    church = 'church'
    other = 'other'


class SocialMediaLink(BaseModel):
    type: SocialMediaType
    url: HttpUrl


class CreateAddress(BaseModel):
    type: str
    building: Optional[str] = None
    unit: Optional[str] = None
    street_number: str
    street: str
    suburb: str
    city: str
    province: str
    country: str
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
              "type": "home",
              "street_number": "21",
              "street": "Allan",
              "suburb": "Noordwyk",
              "city": "Midrand",
              "province": "Johannesburg",
              "country": "South Africa",
              "postal_code": "1685"
            }
        }
    )

class UpdateAddress(BaseModel):
    id: int
    type: Optional[str] = None
    building: Optional[str] = None
    unit: Optional[str] = None
    street_number: Optional[str] = None
    street: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ViewAddress(BaseModel):
    id: int
    type: Optional[str] = None
    building: Optional[str] = None
    unit: Optional[str] = None
    street_number: Optional[str] = None
    street: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PersonProfileFields(BaseModel):
    preferred_name: Optional[str] = None
    middle_name: Optional[str] = None
    title: Optional[str] = None
    biography: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    contact_preferences: Optional[str] = None
    membership_status: Optional[str] = None
    member_since: Optional[CoercedDate] = None
    date_first_attended: Optional[CoercedDate] = None
    baptism_status: Optional[str] = None
    baptism_date: Optional[CoercedDate] = None
    baptism_location: Optional[str] = None
    confirmation_date: Optional[CoercedDate] = None
    previous_church: Optional[str] = None
    membership_transfer_notes: Optional[str] = None
    date_joined: Optional[CoercedDate] = None
    date_membership_ended: Optional[CoercedDate] = None
    reason_for_leaving: Optional[str] = None
    ministry_involvement: Optional[str] = None
    pastoral_notes: Optional[str] = None
    lifecycle_status: Optional[str] = None
    school_grade: Optional[str] = None
    school_name: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    nationality: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    volunteer_status: Optional[str] = None
    skills: Optional[str] = None
    interests: Optional[str] = None
    allergies: Optional[str] = None
    special_requirements: Optional[str] = None
    emergency_notes: Optional[str] = None
    external_image_url: Optional[str] = None


class CreatePerson(PersonProfileFields):
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    date_of_birth: Optional[CoercedDate] = None
    gender: Optional[str] = None
    marriage_date: Optional[CoercedDate] = None
    marital_status: Optional[str] = None
    registered_date: Optional[CoercedDate] = None
    emails: List[PersonEmailInput] = Field(default_factory=list)
    phones: List[PersonPhoneInput] = Field(default_factory=list)
    emergency_contacts: List[EmergencyContactInput] = Field(default_factory=list)
    category_ids: List[int] = Field(default_factory=list)
    service_type_ids: List[int] = Field(default_factory=list)
    custom_fields: List[CustomFieldValueInput] = Field(default_factory=list)
    social_media_links: List[SocialMediaLink] = Field([], title="A list of social media URLs")
    addresses: List[int] = Field([], title="A list of address IDs (normally just one home address)")
    household_ids: Optional[List[int]] = Field(None, title="The list pf ids of the households this person belongs to")
    profile_image_id: Optional[int] = Field(None, title="The profile image of this person")

    @field_validator('date_of_birth','registered_date','marriage_date')
    @classmethod
    def validate_date_in_past(cls, v):
        if v is not None and v > datetime.date.today():
            raise ValueError("Date must be in the past")
        return v

    @model_validator(mode="after")
    def require_a_name(self):
        names = [self.first_name, self.last_name, self.preferred_name]
        if not any(name and str(name).strip() for name in names):
            raise ValueError("Provide a first name, preferred name, or last name")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Joe",
                "last_name": "Soap",
                "email": "test@test.com",
                "mobile_number": "+27721234567",
                "date_of_birth": "1981-01-01",
                "gender": "male",
                "marriage_date": "1981-01-01",
                "marital_status": "single",
                "registered_date": "2022-06-02",
                "household_ids": [1],
                "profile_image_id": 1,
                "social_media_links": [
                    {
                        "type": "linkedin",
                        "url": "https://www.linkedin.com/in/"
                    },
                    {
                        "type": "facebook",
                        "url": "https://www.facebook.com/"
                    }
                ],
                "addresses": [1, 2]
            }
        }
    )


# TODO Investigate if all fields should be optional for the update person model
class UpdatePerson(PersonProfileFields):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    date_of_birth: Optional[CoercedDate] = None
    gender: Optional[str] = None
    marriage_date: Optional[CoercedDate] = None
    marital_status: Optional[str] = None
    registered_date: Optional[CoercedDate] = None
    emails: Optional[List[PersonEmailInput]] = None
    phones: Optional[List[PersonPhoneInput]] = None
    emergency_contacts: Optional[List[EmergencyContactInput]] = None
    category_ids: Optional[List[int]] = None
    service_type_ids: Optional[List[int]] = None
    custom_fields: Optional[List[CustomFieldValueInput]] = None
    social_media_links: List[SocialMediaLink] = Field([], title="A list of social media URLs")
    addresses: List[int] = Field([], title="A list of address IDs (normally just one home address)")
    household_ids: Optional[List[int]] = Field(None, title="The list of ids of the households this person belongs to")
    profile_image_id: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Joe",
                "last_name": "Soap",
                "email": "test@test.com",
                "mobile_number": "+27721234567",
                "date_of_birth": "1981-01-01",
                "gender": "male",
                "marriage_date": "1981-01-01",
                "marital_status": "single",
                "registered_date": "2022-06-02",
                "household_ids": [1],
                "profile_image_id": 1,
                "social_media_links": [
                    {
                        "type": "linkedin",
                        "url": "https://www.linkedin.com/in/"
                    },
                    {
                        "type": "facebook",
                        "url": "https://www.facebook.com/"
                    }
                ],
                "addresses": [1, 2]
            }
        }
    )


class BasicViewPerson(BaseModel):
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    profile_image: Optional[ViewMediaItem] = None
    external_image_url: Optional[str] = None
    date_of_birth: Optional[CoercedDate] = None
    gender: Optional[str] = None


class FullViewPerson(PersonProfileFields, BasicViewPerson):
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    date_of_birth: Optional[CoercedDate] = None
    gender: Optional[str] = None
    marriage_date: Optional[CoercedDate] = None
    marital_status: Optional[str] = None
    registered_date: Optional[CoercedDate] = None
    archived_at: Optional[datetime.datetime] = None
    has_account: bool = False
    emails: List[PersonEmailView] = Field(default_factory=list)
    phones: List[PersonPhoneView] = Field(default_factory=list)
    emergency_contacts: List[EmergencyContactView] = Field(default_factory=list)
    categories: List[CategoryView] = Field(default_factory=list)
    service_types: List[ServiceTypeView] = Field(default_factory=list)
    custom_fields: List[CustomFieldValueView] = Field(default_factory=list)
    relationships: List[RelationshipView] = Field(default_factory=list)
    groups: List[PersonGroupLink] = Field(default_factory=list)
    departments: List[PersonDepartmentLink] = Field(default_factory=list)
    social_media_links: List[SocialMediaLink] = Field([], title="A list of social media URLs")
    addresses: List[ViewAddress] = Field([], title="A list of addresses (normally just one home address)")
    households: Optional[List[ViewHousehold]] = None
    profile_image: Optional[ViewMediaItem] = None
    user: Optional[DisplayUser] = None
    model_config = ConfigDict(from_attributes=True)


try:
    # Importing household first re-enters this module before ViewHousehold exists.
    from src.app.people.models.household import ViewHousehold
    FullViewPerson.model_rebuild()
except ImportError:
    pass
