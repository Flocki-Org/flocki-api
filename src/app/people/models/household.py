from pydantic import BaseModel, Field, root_validator
from .people import ViewAddress, BasicViewPerson

from typing import List

from ...media.models.media import CreateImage


class CreateHousehold(BaseModel):
    id: int = Field(None)
    address_id: int = Field("An address")
    people_ids: List[int] = Field(title="A list of IDs of the people to be added to the household")
    household_image_id: int = Field(None, title="The ID of the image of this household")
    leader_id: int = Field(title="The ID of the leader of the household. If not specified, the leader will be the first person in the household")

    @root_validator
    def validate_leader(cls, values):
        if 'leader_id' not in values:
            raise ValueError("Leader must have an id")
        if values['leader_id'] not in values['people_ids']:
            raise ValueError("Leader must be a member of the household")
        return values

    class Config:
        schema_extra = {
            "example": {
                "leader_id": 1,
                "address_ids": 1,
                "household_image_id": 1,
                "people_ids": [1, 4, 5]
            }
        }


class UpdateHousehold(BaseModel):
    id: int
    address_id: int = Field("An address")
    people_ids: List[int] = Field(title="A list of IDs of the people to be added to the household")
    household_image_id: int = Field(None, title="The ID of the image of this household")
    leader_id: int = Field(
        title="The ID of the leader of the household. If not specified, the leader will be the first person in the household")

    @root_validator
    def validate_leader(cls, values):
        if 'leader_id' not in values:
            raise ValueError("Leader must have an id")
        if values['leader_id'] not in values['people_ids']:
            raise ValueError("Leader must be a member of the household")
        return values

    class Config:
        schema_extra = {
            "example": {
                "leader_id": 1,
                "address_id": 1,
                "household_image_id": 1,
                "people_ids": [1, 4, 5]
            }
        }

class ViewHousehold(BaseModel):
    id: int = Field(None)
    leader: BasicViewPerson = Field(title="The designated leader of the household")
    address: ViewAddress = Field(title="An addresses")
    household_image: CreateImage = Field(None, title="The image of this household")
    people: List[BasicViewPerson] = Field([], title="A list of people belonging to the household")





