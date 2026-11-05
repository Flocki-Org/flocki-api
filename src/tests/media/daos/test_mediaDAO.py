from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.database import Base
from src.app.media.daos.mediaDAO import MediaDAO
from src.app.media.models.database import models
from src.app.people.models.database import models as people_models  # noqa: F401
from src.app.users.models.database import models as user_models  # noqa: F401
from src.app.church.models.database import models as church_models  # noqa: F401
from src.app.worship.models.database import models as worship_models  # noqa: F401

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_media_dao.db"
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
media_dao = MediaDAO(db)


def test_add_and_get_media_item(test_db):
    created = media_dao.add_media_item(
        models.MediaItem(
            store="local",
            address="./media/test.jpg",
            created=datetime(2024, 1, 1),
            filename="test.jpg",
            description="desc",
            content_type="image/jpg",
        )
    )

    fetched = media_dao.get_media_item_by_id(created.id)
    assert fetched.filename == "test.jpg"
    assert fetched.store == "local"


def test_get_media_item_by_id_missing(test_db):
    assert media_dao.get_media_item_by_id(999) is None
