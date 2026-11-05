import pytest
from fastapi_pagination import Params
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.database import Base
from src.app.media.models.database import models as media_models  # noqa: F401
from src.app.people.models.database import models as people_models  # noqa: F401
from src.app.users.models.database import models as user_models  # noqa: F401
from src.app.church.models.database import models as church_models  # noqa: F401
from src.app.worship.daos.songDAO import SongDAO
from src.app.worship.models.database import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_song_dao.db"
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
song_dao = SongDAO(db)


def test_create_song_with_explicit_code(test_db):
    # SQLite does not autoincrement BigInteger PKs used by Song/Author/Sheet.
    song = song_dao.create_song(models.Song(id=1, code="A1", name="Amazing Grace"))
    assert song.id == 1
    assert song.code == "A1"
    assert song_dao.get_song_by_id(song.id).name == "Amazing Grace"


def test_create_song_auto_generates_code(test_db):
    first = song_dao.create_song(models.Song(id=1, name="Alpha"))
    second = song_dao.create_song(models.Song(id=2, name="Amazing"))

    assert first.code == "A1"
    assert second.code == "A2"


def test_create_song_requires_name_for_auto_code(test_db):
    with pytest.raises(ValueError, match="Song name is required"):
        song_dao.create_song(models.Song(id=1, name=None, code=None))


def test_create_song_duplicate_code_raises(test_db):
    song_dao.create_song(models.Song(id=1, code="A1", name="One"))
    with pytest.raises(ValueError, match="Song with that code already exists"):
        song_dao.create_song(models.Song(id=2, code="A1", name="Two"))


def test_get_all_songs_ordered_by_code(test_db):
    song_dao.create_song(models.Song(id=1, code="B1", name="B"))
    song_dao.create_song(models.Song(id=2, code="A1", name="A"))

    page = song_dao.get_all_songs(Params(page=1, size=10))
    assert [song.code for song in page.items] == ["A1", "B1"]


def test_get_song_by_code_and_name(test_db):
    song_dao.create_song(models.Song(id=1, code="A1", name="Amazing Grace"))

    assert song_dao.get_song_by_code("A1").name == "Amazing Grace"
    assert song_dao.get_song_by_name("amazing grace").code == "A1"
    assert song_dao.get_song_by_name("missing") is None


def test_update_song(test_db):
    song = song_dao.create_song(models.Song(id=1, code="A1", name="Old"))
    updated = song_dao.update_song(song, {"name": "New", "id": 999})

    assert updated.name == "New"
    assert updated.id == song.id


def test_author_crud_and_song_links(test_db):
    author = song_dao.create_author(models.Author(id=1, name="Newton"))
    assert song_dao.get_author_by_id(author.id).name == "Newton"
    assert song_dao.get_author_by_name("newton").id == author.id

    updated = song_dao.update_author(author, {"name": "John Newton", "id": 1})
    assert updated.name == "John Newton"
    assert [a.name for a in song_dao.get_all_authors()] == ["John Newton"]

    song = song_dao.create_song(models.Song(id=1, code="A1", name="Amazing Grace"))
    song_dao.create_author_song(song, updated)
    db.commit()

    existing = song_dao.get_existing_authors_for_song(song.id)
    assert len(existing) == 1
    song_dao.delete_author_song(existing[0].id)
    db.commit()
    assert song_dao.get_existing_authors_for_song(song.id) == []


def test_create_author_duplicate_name_raises(test_db):
    song_dao.create_author(models.Author(id=1, name="Newton"))
    with pytest.raises(ValueError, match="Author with that name already exists"):
        song_dao.create_author(models.Author(id=2, name="Newton"))


def test_create_sheet_via_song_dao(test_db):
    song = song_dao.create_song(models.Song(id=1, code="A1", name="Song"))
    media = media_models.MediaItem(
        store="local", address="./a.pdf", created=__import__("datetime").datetime.now(), filename="a.pdf"
    )
    db.add(media)
    db.commit()
    db.refresh(media)

    sheet = song_dao.create_sheet(
        models.Sheet(id=1, type="LYRICS", sheet_key="G", song_id=song.id, media_item_id=media.id)
    )
    assert sheet.id == 1
