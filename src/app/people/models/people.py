from __future__ import annotations

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, field_validator
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
from src.app.media.models.media import CreateMediaItem, ViewMediaItem
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
    business = 'business'
    student_accommodation = 'student_accommodation'
    church = 'church'


class SocialMediaLink(BaseModel):
    type: SocialMediaType
    url: HttpUrl


class CreateAddress(BaseModel):
    type: AddressType
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
    type: Optional[AddressType] = None
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
    type: Optional[AddressType] = None
    street_number: Optional[str] = None
    street: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CreatePerson(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    mobile_number: str
    date_of_birth: Optional[CoercedDate] = None
    gender: Optional[Gender] = None
    marriage_date: Optional[CoercedDate] = None
    marital_status: Optional[MaritalStatus] = None
    registered_date: Optional[CoercedDate] = None
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
class UpdatePerson(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    date_of_birth: Optional[CoercedDate] = None
    gender: Optional[Gender] = None
    marriage_date: Optional[CoercedDate] = None
    marital_status: Optional[MaritalStatus] = None
    registered_date: Optional[CoercedDate] = None
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
    date_of_birth: Optional[CoercedDate] = None
    gender: Optional[Gender] = None


class FullViewPerson(BasicViewPerson):
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    date_of_birth: Optional[CoercedDate] = None
    gender: Optional[Gender] = None
    marriage_date: Optional[CoercedDate] = None
    marital_status: Optional[MaritalStatus] = None
    registered_date: Optional[CoercedDate] = None
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
