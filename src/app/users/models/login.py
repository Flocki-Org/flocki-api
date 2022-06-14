from typing import Optional

from pydantic import BaseModel

# move to env var
class Login(BaseModel):
    username: str
    password: str

    class Config:
            schema_extra={
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
