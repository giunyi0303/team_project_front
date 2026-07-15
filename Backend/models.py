from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False)
    views = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    post = relationship("Post", back_populates="comments")


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
