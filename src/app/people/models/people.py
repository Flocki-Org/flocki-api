from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, HttpUrl, validator
import datetime
from enum import Enum
from typing import List, ForwardRef, Optional

# from src.app.people.models.household import Household
from src.app.media.models.media import CreateMediaItem, ViewMediaItem
from src.app.users.models.user import DisplayUser

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
    postal_code: str = Field(None)
    latitude: float = Field(None)
    longitude: float = Field(None)

    class Config:
        schema_extra = {
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

class UpdateAddress(BaseModel):
    id: int
    type: AddressType = Field(None)
    street_number: str = Field(None)
    street: str = Field(None)
    suburb: str = Field(None)
    city: str = Field(None)
    province: str = Field(None)
    country: str = Field(None)
    postal_code: str = Field(None)
    latitude: float = Field(None)
    longitude: float = Field(None)


class ViewAddress(BaseModel):
    id: int
    type: AddressType = Field(None)
    street_number: str = Field(None)
    street: str = Field(None)
    suburb: str = Field(None)
    city: str = Field(None)
    province: str = Field(None)
    country: str = Field(None)
    postal_code: str = Field(None)
    latitude: float = Field(None)
    longitude: float = Field(None)


class CreatePerson(BaseModel):
    id: int = Field(None)
    first_name: str
    last_name: str
    email: EmailStr = Field(None)
    mobile_number: str
    date_of_birth: datetime.date = Field(None)
    gender: Gender = Field(None)
    marriage_date: datetime.date = Field(None)
    marital_status: MaritalStatus = Field(None)
    registered_date: datetime.date = Field(None)
    social_media_links: List[SocialMediaLink] = Field([], title="A list of social media URLs")
    addresses: List[int] = Field([], title="A list of address IDs (normally just one home address)")
    household_ids: List[int] = Field(None, title="The list pf ids of the households this person belongs to")
    profile_image_id: int = Field(None, title="The profile image of this person")

    @validator('date_of_birth','registered_date','marriage_date')
    def validate_date_in_past(cls, v):
        if v > datetime.date.today():
            raise ValueError("Date must be in the past")
        return v

    class Config:
        schema_extra = {
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


# TODO Investigate if all fields should be optional for the update person model
class UpdatePerson(BaseModel):
    id: int
    first_name: str = Field(None)
    last_name: str = Field(None)
    email: EmailStr = Field(None)
    mobile_number: str = Field(None)
    date_of_birth: datetime.date = Field(None)
    gender: Gender = Field(None)
    marriage_date: datetime.date = Field(None)
    marital_status: MaritalStatus = Field(None)
    registered_date: datetime.date = Field(None)
    social_media_links: List[SocialMediaLink] = Field([], title="A list of social media URLs")
    addresses: List[int] = Field([], title="A list of address IDs (normally just one home address)")
    household_ids: List[int] = Field(None, title="The list of ids of the households this person belongs to")
    profile_image_id: int = Field(None)

    class Config:
        schema_extra = {
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


class BasicViewPerson(BaseModel):
    id: int = Field(None)
    first_name: str = Field(None)
    last_name: str = Field(None)
    email: EmailStr = Field(None)
    mobile_number: str = Field(None)
    profile_image: ViewMediaItem = Field(None)
    date_of_birth: datetime.date = Field(None)
    gender: Gender = Field(None)


class FullViewPerson(BasicViewPerson):
    email: EmailStr = Field(None)
    mobile_number: str = Field(None)
    date_of_birth: datetime.date = Field(None)
    gender: Gender = Field(None)
    marriage_date: datetime.date = Field(None)
    marital_status: MaritalStatus = Field(None)
    registered_date: datetime.date = Field(None)
    social_media_links: List[SocialMediaLink] = Field([], title="A list of social media URLs")
    addresses: List[ViewAddress] = Field([], title="A list of addresses (normally just one home address)")
    households: List[ViewHousehold] = Field(None)
    profile_image: ViewMediaItem = Field(None)
    user: DisplayUser = Field(None)
    class Config:
        orm_mode = True


from src.app.people.models.household import ViewHousehold
FullViewPerson.update_forward_refs(household=ViewHousehold)
