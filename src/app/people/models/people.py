from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, HttpUrl
import datetime
from enum import Enum
from typing import List, ForwardRef

#from src.app.people.models.household import Household
from src.app.media.models.media import Image, DisplayImage

Household = ForwardRef('Household')

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

class Address(BaseModel):
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

class AddressOpt(BaseModel):
    id: int = Field(None)
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

class Person(BaseModel):
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
    addresses: List[Address] = Field([], title="A list of addresses (normally just one home address)")
    household_id: int = Field(None)
    household: Household = Field(None, title="The household this person belongs to")
    profile_image: Image = Field(None, title="The profile image of this person")
    class Config:
            schema_extra={
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


class PersonOpt(BaseModel):
    id: int = Field(None)
    first_name: str = Field(None)
    last_name: str = Field(None)
    email: EmailStr = Field(None)
    mobile_number: str = Field(None)
    date_of_birth: datetime.date = Field(None)
    gender: Gender = Field(None)
    marriage_date: datetime.date = Field(None)
    marital_status: MaritalStatus = Field(None)
    registered_date: datetime.date = Field(None)
    social_media_links: List[SocialMediaLink] = Field(None, title="A list of social media URLs")
    addresses: List[Address] = Field([], title="A list of addresses (normally just one home address)")
    class Config:
        orm_mode = True

class DisplayHouseholdPerson(BaseModel):
    id: int = Field(None)
    first_name: str = Field(None)
    last_name: str = Field(None)
    email: EmailStr = Field(None)
    mobile_number: str = Field(None)
    date_of_birth: datetime.date = Field(None)
    gender: Gender = Field(None)
    marriage_date: datetime.date = Field(None)
    marital_status: MaritalStatus = Field(None)
    registered_date: datetime.date = Field(None)
    social_media_links: List[SocialMediaLink] = Field(None, title="A list of social media URLs")
    addresses: List[Address] = Field([], title="A list of addresses (normally just one home address)")
    class Config:
        orm_mode = True

class DisplayPersonHousehold(BaseModel):
    id: int = Field(None)
    leader: DisplayHouseholdPerson
    address: Address = Field(title="The household address")
    people: List[DisplayHouseholdPerson] = Field([], title="A list of people belonging to the household")
    class Config:
        orm_mode = True

class DisplayPerson(BaseModel):
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
    social_media_links: List[SocialMediaLink] = Field(None, title="A list of social media URLs")
    addresses: List[Address] = Field([], title="A list of addresses (normally just one home address)")
    household: DisplayPersonHousehold = Field(None)
    profile_image: Image = Field(None)
    class Config:
        orm_mode = True

class DisplayPersonProfileImage(BaseModel):
    id: int = Field(None)
    profile_image: DisplayImage = Field(None)
    class Config:
        orm_mode = True

from src.app.people.models.household import Household
Person.update_forward_refs()