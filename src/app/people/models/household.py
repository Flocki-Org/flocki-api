from pydantic import BaseModel, EmailStr, Field
import datetime
from .people import PersonOpt, AddressOpt, CreateAddress, BasicViewPerson

from typing import List

from ...media.models.media import DisplayImage, Image


class Household(BaseModel):
    id: int = Field(None)
    leader: BasicViewPerson = Field(title="The designated leader of the household")
    address: AddressOpt = Field(title="An addresses")
    household_image: Image = Field(None, title="The image of this household")
    people: List[BasicViewPerson] = Field([], title="A list of people belonging to the household")


#Household.update_forward_refs()


class CreateHousehold(BaseModel):
    id: int = Field(None)
    leader: PersonOpt = Field(None, title="The leader of the household. If not specified, the leader will be the first person in the household")
    address: AddressOpt = Field("An address")
    people: List[PersonOpt] = Field(title="A list of the people to be added to the household")
    household_image: DisplayImage = Field(None, title="The image of this household")

    class Config:
            schema_extra={
                  "example": {
                  "leader": {"id": 1},
                  "address": {"id": 1},
                  "household_image": {"id": 1},
                  "people": [
                      {"id": 1},
                      {"id": 4},
                      {"id": 5}]
                    }
                }

class DisplayHousehold(BaseModel):
    id: int = Field(None)
    leader: BasicViewPerson
    address: CreateAddress = Field(title="The household address")
    people: List[BasicViewPerson] = Field([], title="A list of people belonging to the household")
    household_image: DisplayImage = Field(None)

    class Config:
        orm_mode = True


class DisplayHouseholdImage(BaseModel):
    id: int = Field(None)
    household_image: DisplayImage = Field(None)

    class Config:
        orm_mode = True





