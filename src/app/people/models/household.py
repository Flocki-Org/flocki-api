from pydantic import BaseModel, EmailStr, Field
import datetime
from .people import ViewAddress, CreateAddress, BasicViewPerson

from typing import List

from ...media.models.media import ViewImage, CreateImage


class ViewHousehold(BaseModel):
    id: int = Field(None)
    leader: BasicViewPerson = Field(title="The designated leader of the household")
    address: ViewAddress = Field(title="An addresses")
    household_image: CreateImage = Field(None, title="The image of this household")
    people: List[BasicViewPerson] = Field([], title="A list of people belonging to the household")


class CreateHousehold(BaseModel):
    id: int = Field(None)
    leader: int = Field(None, title="The ID of the leader of the household. If not specified, the leader will be the first person in the household")
    address: int = Field("An address")
    people: List[int] = Field(title="A list of IDs of the people to be added to the household")
    household_image: int = Field(None, title="The ID of the image of this household")

    class Config:
            schema_extra={
                  "example": {
                  "leader": 1,
                  "address": 1,
                  "household_image": 1,
                  "people": [1, 4, 5]
                    }
                }




