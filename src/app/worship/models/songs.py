# create pydantic models for songs
from typing import List

from pydantic import BaseModel, Field
from src.app.media.models.media import ViewMediaItem

class CreateSong(BaseModel):
    code: str = Field(None, title="The code of the song")
    name: str = Field(None, title="The name of the song")
    secondary_name: str = Field(None, title="The secondary name of the song")
    song_key: str = Field(None, title="The key of the song")
    artist_id: int = Field(None, title="The artist id of the song")
    style: str = Field(None, title="The style of the song")
    tempo: str = Field(None, title="The tempo of the song")
    ccli_number: str = Field(None, title="The ccli number of the song")
    video_link: str = Field(None, title="The video link of the song")

class CreateSheet(BaseModel):
    type: str = Field(None, title="The type of the sheet")
    song_id: int = Field(None, title="The song id of the sheet")
    sheet_key: str = Field(None, title="The key of the sheet")
    media_item_id: int = Field(None, title="The media item id of the sheet")

class ViewSheet(BaseModel):
    id: int = Field(None, title="The id of the sheet")
    type: str = Field(None, title="The type of the sheet")
    sheet_key: str = Field(None, title="The key of the sheet")
    song_id: int = Field(None, title="The song id of the sheet")
    media_item: ViewMediaItem = Field(None, title="The media item of the sheet")

class CreateArtist(BaseModel):
    name: str = Field(None, title="The name of the artist")

class ViewArtist(BaseModel):
    id: int = Field(None, title="The id of the artist")
    name: str = Field(None, title="The name of the artist")


class ViewSong(BaseModel):
    id: int = Field(None, title="The id of the song")
    code: str = Field(None, title="The code of the song")
    name: str = Field(None, title="The name of the song")
    secondary_name: str = Field(None, title="The secondary name of the song")
    song_key: str = Field(None, title="The key of the song")
    artist_id: int = Field(None, title="The artist id of the song")
    style: str = Field(None, title="The style of the song")
    tempo: str = Field(None, title="The tempo of the song")
    ccli_number: str = Field(None, title="The ccli number of the song")
    video_link: str = Field(None, title="The video link of the song")
    sheets: List[ViewSheet] = Field(None, title="The sheets of the song")
