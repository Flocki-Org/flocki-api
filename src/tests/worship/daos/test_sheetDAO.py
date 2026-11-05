from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.database import Base
from src.app.media.models.database import models as media_models
from src.app.people.models.database import models as people_models  # noqa: F401
from src.app.users.models.database import models as user_models  # noqa: F401
from src.app.church.models.database import models as church_models  # noqa: F401
from src.app.worship.daos.sheetDAO import SheetDAO
from src.app.worship.models.database import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sheet_dao.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


db = next(override_get_db())
sheet_dao = SheetDAO(db)


def _song_and_media():
    # SQLite does not autoincrement BigInteger PKs used by Song/Sheet.
    song = models.Song(id=1, code="A1", name="Song")
    media = media_models.MediaItem(store="local", address="./a.pdf", created=datetime.now(), filename="a.pdf")
    db.add(song)
    db.add(media)
    db.commit()
    db.refresh(song)
    db.refresh(media)
    return song, media


def test_create_and_get_sheet(test_db):
    song, media = _song_and_media()
    sheet = sheet_dao.create_sheet(
        models.Sheet(id=1, type="LYRICS", sheet_key="G", song_id=song.id, media_item_id=media.id)
    )

    fetched = sheet_dao.get_sheet_by_id(sheet.id)
    assert fetched.type == "LYRICS"
    assert sheet_dao.get_song_sheet(song.id, "LYRICS", "G").id == sheet.id


def test_create_sheet_duplicate_raises(test_db):
    song, media = _song_and_media()
    sheet_dao.create_sheet(
        models.Sheet(id=1, type="LYRICS", sheet_key="G", song_id=song.id, media_item_id=media.id)
    )

    with pytest.raises(ValueError, match="Sheet with that type and key already exists"):
        sheet_dao.create_sheet(
            models.Sheet(id=2, type="LYRICS", sheet_key="G", song_id=song.id, media_item_id=media.id)
        )


def test_update_sheet(test_db):
    song, media = _song_and_media()
    other_media = media_models.MediaItem(store="local", address="./b.pdf", created=datetime.now(), filename="b.pdf")
    db.add(other_media)
    db.commit()
    db.refresh(other_media)

    sheet = sheet_dao.create_sheet(
        models.Sheet(id=1, type="LYRICS", sheet_key="G", song_id=song.id, media_item_id=media.id)
    )
    sheet.media_item_id = other_media.id
    updated = sheet_dao.update_sheet(sheet)

    assert updated.media_item_id == other_media.id
