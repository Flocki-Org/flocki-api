from typing import Optional

from pydantic import BaseModel, EmailStr, Field
import datetime

from src.app.media.models.media import ViewMediaItem
from src.app.people.models.people import ViewAddress
from src.app.utils.httpUrl import HttpUrl

class CreateChurch(BaseModel):
    website: Optional[HttpUrl] = Field(None, title="The church website")
    email: Optional[EmailStr] = Field(None, title="The church email")
    phone: Optional[str] = Field(None, title="The church phone number")
    address_id: Optional[int] = Field(None, title="The address id of the church")
    logo_image_id: Optional[int] = Field(None, title="The logo of this church")
    name: str
    description: Optional[str] = None

# add endpoint to get church
class ViewChurch(BaseModel):
    id: Optional[int] = None
    created: Optional[datetime.datetime] = None
    website: Optional[HttpUrl] = Field(None, title="The church website")
    email: Optional[EmailStr] = Field(None, title="The church email")
    phone: Optional[str] = Field(None, title="The church phone number")
    address: Optional[ViewAddress] = Field(None, title="The address id of the church")
    logo_image: Optional[ViewMediaItem] = Field(None, title="The logo of this church")
    name: str
    description: Optional[str] = None

class UpdateChurch(BaseModel):
    id: Optional[int] = None
    website: Optional[HttpUrl] = Field(None, title="The church website")
    email: Optional[EmailStr] = Field(None, title="The church email")
    phone: Optional[str] = Field(None, title="The church phone number")
    address_id: Optional[int] = Field(None, title="The address id of the church")
    logo_image_id: Optional[int] = Field(None, title="The logo id of this church")
    name: str
    description: Optional[str] = None
