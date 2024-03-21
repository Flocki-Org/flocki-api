from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import BigInteger
from src.app.database import Base

class Song(Base):
    __tablename__ = 'songs'
    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String)
    name = Column(String)
    secondary_name = Column(String)
    song_key = Column(String)
    style = Column(String)
    tempo = Column(String)
    ccli_number = Column(String)
    video_link = Column(String)
    sheets = relationship("Sheet", backref="song")
    authors = relationship("AuthorSong", back_populates="song", cascade="all, delete-orphan")

    # unique key code
    __table_args__ = (UniqueConstraint('code', name='songs_code_uc'),)

class Author(Base):
    __tablename__ = 'authors'
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String)
    __table_args__ = (UniqueConstraint('name', name='authors_name_uc'),)

class AuthorSong(Base):
    __tablename__ = 'author_songs'
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    song_id = Column(Integer, ForeignKey('songs.id'), nullable=False)
    song = relationship("Song", back_populates="authors")
    author = relationship("Author")
    _table_args__ = (UniqueConstraint('author_id', 'song_id', name='authorsong_author_song_uc'))

class Sheet(Base):
    __tablename__ = 'sheets'
    id = Column(BigInteger, primary_key=True, index=True)
    type = Column(String)
    sheet_key = Column(String)
    song_id = Column(Integer, ForeignKey('songs.id'))
    media_item_id = Column(Integer, ForeignKey('media_items.id'))
    media_item = relationship("MediaItem", backref="sheets")
    # combination of type and song_id must be unique
    __table_args__ = (UniqueConstraint('type', 'song_id', 'sheet_key', name='sheets_type_song_id_sheet_key_uc'),)
