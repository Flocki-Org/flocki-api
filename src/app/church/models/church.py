from pydantic import HttpUrl, BaseModel, Field, EmailStr
import datetime

from src.app.media.models.media import ViewImage
from src.app.people.models.people import ViewAddress


class CreateChurch(BaseModel):
    id: int = None
    website: HttpUrl = Field(None, title="The church website")
    email: EmailStr = Field(None, title="The church email")
    phone: str = Field(None, title="The church phone number")
    address_id: int = Field(None, title="The address id of the church")
    logo_image_id: int = Field(None, title="The logo of this church")
    name: str
    description: str = None

# add endpoint to get church
class ViewChurch(BaseModel):
    id: int = None
    created: datetime.datetime = None
    website: HttpUrl = Field(None, title="The church website")
    email: EmailStr = Field(None, title="The church email")
    phone: str = Field(None, title="The church phone number")
    address_id: ViewAddress = Field(None, title="The address id of the church")
    logo_image: ViewImage = Field(None, title="The logo of this church")
    name: str
    description: str = None

class UpdateChurch(BaseModel):
    id: int = None
    website: HttpUrl = Field(None, title="The church website")
    email: EmailStr = Field(None, title="The church email")
    phone: str = Field(None, title="The church phone number")
    address_id: ViewAddress = Field(None, title="The address id of the church")
    logo_image: ViewImage = Field(None, title="The logo of this church")
    name: str
    description: str = None