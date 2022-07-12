from pydantic import BaseModel, EmailStr, Field, HttpUrl
import datetime
from enum import Enum
from typing import List

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
    class Config:
        orm_mode = True

