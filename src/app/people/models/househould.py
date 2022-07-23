from pydantic import BaseModel, EmailStr, Field, HttpUrl
import datetime
from .person import DisplayPerson, Person, Address
from enum import Enum
from typing import List

class Household(BaseModel):
    id: int = Field(None)
    leader: Person = Field(title="The designated leader of the household")
    address: Address = Field(title="A list of addresses (normally just one home address)")
    people: List[Person]

class DisplayHousehold(BaseModel):
    id: int = Field(None)
    leader: DisplayPerson
    address: Address = Field(title="The household address")
    people: List[DisplayPerson] = Field([], title="A list of people belonging to the household")
    class Config:
        orm_mode = True

