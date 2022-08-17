from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, HttpUrl
import datetime
from enum import Enum
from typing import List, ForwardRef

# from src.app.people.models.household import Household
from src.app.media.models.media import Image, DisplayImage

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


class SocialMediaLink(BaseModel):
    type: SocialMediaType
    url: HttpUrl


class CreateAddress(BaseModel):
    id: int = Field(None)
    type: AddressType
    streetNumber: str
    street: str
    suburb: str
    city: str
    province: str
    country: str
    postalCode: str = Field(None)
    latitude: float = Field(None)
    longitude: float = Field(None)


class UpdateAddress(BaseModel):
    id: int
    type: AddressType = Field(None)
    streetNumber: str = Field(None)
    street: str = Field(None)
    suburb: str = Field(None)
    city: str = Field(None)
    province: str = Field(None)
    country: str = Field(None)
    postalCode: str = Field(None)
    latitude: float = Field(None)
    longitude: float = Field(None)


# This class is used when creating an entity that has an address previously created. Only the ID needs to be sent.
class AddressOpt(BaseModel):
    id: int
    type: AddressType = Field(None)
    streetNumber: str = Field(None)
    street: str = Field(None)
    suburb: str = Field(None)
    city: str = Field(None)
    province: str = Field(None)
    country: str = Field(None)
    postalCode: str = Field(None)
    latitude: float = Field(None)
    longitude: float = Field(None)


class CreatePerson(BaseModel):
    id: int = Field(None)
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str
    date_of_birth: datetime.date
    gender: Gender = Field(None)
    marriage_date: datetime.date
    marital_status: MaritalStatus = Field(None)
    registered_date: datetime.date
    social_media_links: List[SocialMediaLink] = Field([], title="A list of social media URLs")
    addresses: List[CreateAddress] = Field([], title="A list of addresses (normally just one home address)")
    household_id: int = Field(None, title="The id of the household this person belongs to")
    profile_image_id: int = Field(None, title="The profile image of this person")

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
                "household_id": 1,
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
                "addresses": [
                    {
                        "type": "home",
                        "streetNumber": "99",
                        "street": "3rd Avenue",
                        "suburb": "Bryanston",
                        "city": "Johannesburg",
                        "province": "Gauteng",
                        "country": "South Africa",
                        "postalCode": "2191"
                    }]
            }
        }


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
    addresses: List[CreateAddress] = Field([], title="A list of addresses (normally just one home address)")
    household_id: int = Field(None)
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
                "household_id": 1,
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
                "addresses": [
                    {
                        "type": "home",
                        "streetNumber": "99",
                        "street": "3rd Avenue",
                        "suburb": "Bryanston",
                        "city": "Johannesburg",
                        "province": "Gauteng",
                        "country": "South Africa",
                        "postalCode": "2191"
                    }]
            }
        }


# Can be used when person has previously been created. e.g. when creating a household.
class PersonOpt(BaseModel):
    id: int = Field(None)

    class Config:
        orm_mode = True


# Can be used when person has previously been created. e.g. when creating a household.
class BasicViewPerson(BaseModel):
    id: int = Field(None)
    first_name: str = Field(None)
    last_name: str = Field(None)


# class DisplayPersonHousehold(BaseModel):
#     id: int = Field(None)
#     leader: BasicViewPerson
#     address: CreateAddress = Field(title="The household address")
#     people: List[BasicViewPerson] = Field([], title="A list of people belonging to the household")
#
#     class Config:
#         orm_mode = True


class ProfileImageViewPerson(BasicViewPerson):
    profile_image: DisplayImage = Field(None)

    class Config:
        orm_mode = True



class FullViewPerson(BasicViewPerson):
    email: EmailStr = Field(None)
    mobile_number: str = Field(None)
    date_of_birth: datetime.date = Field(None)
    gender: Gender = Field(None)
    marriage_date: datetime.date = Field(None)
    marital_status: MaritalStatus = Field(None)
    registered_date: datetime.date = Field(None)
    social_media_links: List[SocialMediaLink] = Field([], title="A list of social media URLs")
    addresses: List[CreateAddress] = Field([], title="A list of addresses (normally just one home address)")
    household: Household = Field(None)
    profile_image: DisplayImage = Field(None)

    class Config:
        orm_mode = True

from src.app.people.models.household import Household
FullViewPerson.update_forward_refs(household=Household)
