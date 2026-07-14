from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False)
    views = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String(50), unique=True, index=True, nullable=False)
    region = Column(String(30), nullable=False)
    category = Column(String(50), index=True, nullable=False)
    content_type_id = Column(String(10))

    title = Column(String(300), index=True, nullable=False)
    address = Column(String(500))
    address_detail = Column(String(300))
    zipcode = Column(String(30))
    telephone = Column(String(100))

    longitude = Column(Float)
    latitude = Column(Float)

    image_url = Column(Text)
    thumbnail_url = Column(Text)
    copyright_type = Column(String(30))
    created_time = Column(String(30))
    modified_time = Column(String(30))
