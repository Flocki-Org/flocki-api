from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

class User(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str
    password: str
    person_id: Optional[int] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Joe",
                "last_name": "Soap",
                "email": "test@test.com",
                "mobile_number": "+27721234567",
                "password": "password"
            }
        }
    )

class DisplayUser(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: Optional[str] = None
    person_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
