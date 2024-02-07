from typing import List

from fastapi import status, Depends, HTTPException, UploadFile, APIRouter
from fastapi_pagination import Params, Page

from src.app.media.models.media import ViewMediaItem
from src.app.worship.models.songs import ViewSong

from src.app.worship.services.songService import SongService, NoSongException, SongWithThatCodeExists
from src.app.worship.services.sheetService import SheetService, NoSongException as NSException
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user

router = APIRouter(tags=['Songs'])

@router.get('/song/{id}', response_model=ViewSong)
def get_song(id: int, song_service: SongService = Depends(SongService)):
    try:
        song = song_service.get_song_by_id(id)
        if song is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The song does not exist")
        return song
    except NoSongException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song with that id does not exist")

@router.get('/songs', response_model=Page[ViewSong])
def get_songs(page: int = 1, page_size:int = 10, song_service : SongService = Depends(SongService)):
    return song_service.get_all_songs()

@router.post('/song', response_model=ViewSong)
def create_song(song: ViewSong, song_service: SongService = Depends(SongService)):
    try:
        return song_service.create_song(song)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SongWithThatCodeExists as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put('/song_sheet', response_model=ViewSong)
def upload_song_sheet(song_id: int, type: str, sheet_key: str,  file: UploadFile, sheet_service : SheetService = Depends(SheetService),
                  current_user: User = Depends(get_current_user)):
    try:
        song_sheet_response = sheet_service.upload_song_sheet(song_id, type, sheet_key, file);
        return song_sheet_response;
    except NSException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song with that id does not exist")

#endpoint to get a sheet by song id, for a given type and given song key unless key not provided use song_key of song
@router.get('/song_sheet/{song_id}/{type}/{sheet_key}')
def get_song_sheet(song_id: int, type: str, sheet_key: str = None, sheet_service : SheetService = Depends(SheetService)):
    try:
        sheet = sheet_service.get_song_sheet(song_id, type, sheet_key)
        if sheet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The sheet does not exist")
        return sheet
    except NSException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song with that id does not exist")

#endpoint to get a sheet by song id, for a given type and given song key unless key not provided use song_key of song
@router.get('/song_sheet/{song_id}/{type}')
def get_song_sheet(song_id: int, type: str, sheet_service : SheetService = Depends(SheetService)):
    try:
        sheet = sheet_service.get_song_sheet(song_id, type, None)
        if sheet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The sheet does not exist")
        return sheet
    except NSException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song with that id does not exist")
