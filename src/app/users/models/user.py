from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    id: int = Field(None)
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str
    password: str
    person_id: int = Field(None)
    class Config:
            schema_extra={
                  "example": {
                  "first_name": "Joe",
                  "last_name": "Soap",
                  "email": "test@test.com",
                  "mobile_number": "+27721234567",
                  "password": "password"
                }
            }

class DisplayUser(BaseModel):
    id: int = Field(None)
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str = Field(None)
    person_id: int = Field(None)

    class Config:
        orm_mode = True

