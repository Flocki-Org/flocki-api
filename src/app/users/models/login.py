from typing import Optional

from pydantic import BaseModel, Field
from src.app.people.models.people import BasicViewPerson
from src.app.users.models.user import DisplayUser


# move to env var
class Login(BaseModel):
    username: str
    password: str

    class Config:
        schema_extra = {
            "example": {
                "username": "joe@test.com",
                "password": "password"
            }
        }


class DisplayLogin(BaseModel):
    username: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: DisplayUser
    person: BasicViewPerson = Field(None)
