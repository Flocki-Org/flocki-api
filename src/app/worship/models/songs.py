# create pydantic models for songs
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field
from src.app.media.models.media import ViewMediaItem

class SheetType(str, Enum):
    LYRICS = "LYRICS"
    GUITAR = "GUITAR"
    LEAD = "LEAD"
    PIANO = "PIANO"

class CreateSong(BaseModel):
    code: Optional[str] = Field(None, title="The code of the song")
    name: Optional[str] = Field(None, title="The name of the song")
    secondary_name: Optional[str] = Field(None, title="The secondary name of the song")
    song_key: Optional[str] = Field(None, title="The key of the song")
    style: Optional[str] = Field(None, title="The style of the song")
    tempo: Optional[str] = Field(None, title="The tempo of the song")
    ccli_number: Optional[str] = Field(None, title="The ccli number of the song")
    video_link: Optional[str] = Field(None, title="The video link of the song")
    author_ids: Optional[List[int]] = Field(None, title="The list of ids of the Authors who wrote this song")

class CreateSheet(BaseModel):
    type: Optional[SheetType] = Field(None, title="The type of the sheet")
    song_id: Optional[int] = Field(None, title="The song id of the sheet")
    sheet_key: Optional[str] = Field(None, title="The key of the sheet")
    media_item_id: Optional[int] = Field(None, title="The media item id of the sheet")

class ViewSheet(BaseModel):
    id: Optional[int] = Field(None, title="The id of the sheet")
    type: Optional[SheetType] = Field(None, title="The type of the sheet")
    sheet_key: Optional[str] = Field(None, title="The key of the sheet")
    song_id: Optional[int] = Field(None, title="The song id of the sheet")
    media_item: Optional[ViewMediaItem] = Field(None, title="The media item of the sheet")

class CreateAuthor(BaseModel):
    name: Optional[str] = Field(None, title="The name of the author")

class ViewAuthor(BaseModel):
    id: Optional[int] = Field(None, title="The id of the author")
    name: Optional[str] = Field(None, title="The name of the author")

class ViewSong(BaseModel):
    id: Optional[int] = Field(None, title="The id of the song")
    code: Optional[str] = Field(None, title="The code of the song")
    name: Optional[str] = Field(None, title="The name of the song")
    secondary_name: Optional[str] = Field(None, title="The secondary name of the song")
    song_key: Optional[str] = Field(None, title="The key of the song")
    style: Optional[str] = Field(None, title="The style of the song")
    tempo: Optional[str] = Field(None, title="The tempo of the song")
    ccli_number: Optional[str] = Field(None, title="The ccli number of the song")
    video_link: Optional[str] = Field(None, title="The video link of the song")
    sheets: Optional[List[ViewSheet]] = Field(None, title="The sheets of the song")
    authors: List[ViewAuthor] = Field([], title="A list of authors")
