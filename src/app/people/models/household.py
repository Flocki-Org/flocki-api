from pydantic import BaseModel, Field, root_validator
from .people import ViewAddress, BasicViewPerson

from typing import List

from ...media.models.media import CreateImage


class CreateHousehold(BaseModel):
    id: int = Field(None)
    address: int = Field("An address")
    people: List[int] = Field(title="A list of IDs of the people to be added to the household")
    household_image: int = Field(None, title="The ID of the image of this household")
    leader: int = Field(None,
                        title="The ID of the leader of the household. If not specified, the leader will be the first person in the household")
    @root_validator
    def validate_leader(cls, values):
        if values['leader'] is None:
            raise ValueError("Leader must have an id")
        if values['leader'] not in values['people']:
            raise ValueError("Leader must be a member of the household")
        return values

    class Config:
        schema_extra = {
            "example": {
                "leader": 1,
                "address": 1,
                "household_image": 1,
                "people": [1, 4, 5]
            }
        }


class ViewHousehold(BaseModel):
    id: int = Field(None)
    leader: BasicViewPerson = Field(title="The designated leader of the household")
    address: ViewAddress = Field(title="An addresses")
    household_image: CreateImage = Field(None, title="The image of this household")
    people: List[BasicViewPerson] = Field([], title="A list of people belonging to the household")





