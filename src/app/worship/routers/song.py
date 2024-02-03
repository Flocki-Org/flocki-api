from fastapi import status, Depends, HTTPException, UploadFile, APIRouter

from src.app.worship.models.songs import ViewSong

from src.app.worship.services.songService import SongService, NoSongException
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
