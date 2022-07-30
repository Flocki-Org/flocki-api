from pydantic import BaseModel, EmailStr, Field
import datetime
from .people import SocialMediaLink, Gender, MaritalStatus, PersonOpt, Person, AddressOpt, Address
#from .people import PersonOpt, Person, AddressOpt, Address

from typing import List

class Household(BaseModel):
    id: int = Field(None)
    leader: Person = Field(title="The designated leader of the household")
    address: Address = Field(title="An addresses")
    people: List[Person]

Household.update_forward_refs()
class CreateHousehold(BaseModel):
    id: int = Field(None)
    leader: PersonOpt = Field(None, title="The leader of the household. If not specified, the leader will be the first person in the household")
    address: AddressOpt = Field("An addresses")
    people: List[PersonOpt] = Field(title="A list of the people to be added to the household")

    class Config:
            schema_extra={
                  "example": {
                  "leader": {"id": 1},
                  "address": {"id": 1},
                  "people": [
                      {"id": 1},
                      {"id": 4},
                      {"id": 5}]
                    }
                }

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

class DisplayHousehold(BaseModel):
    id: int = Field(None)
    leader: DisplayHouseholdPerson
    address: Address = Field(title="The household address")
    people: List[DisplayHouseholdPerson] = Field([], title="A list of people belonging to the household")
    class Config:
        orm_mode = True



