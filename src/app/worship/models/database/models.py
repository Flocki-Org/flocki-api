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
    artist_id = Column(Integer, ForeignKey('artists.id'))
    style = Column(String)
    tempo = Column(String)
    ccli_number = Column(String)
    video_link = Column(String)
    artist = relationship("Artist", backref="songs")
    sheets = relationship("Sheet", backref="song")
    # unique key code
    __table_args__ = (UniqueConstraint('code', name='songs_code_uc'),)

class Artist(Base):
    __tablename__ = 'artists'
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String)

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
