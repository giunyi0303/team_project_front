from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    password: str = Field(min_length=1, max_length=100)


class PostUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    password: str = Field(min_length=1, max_length=100)


class PasswordRequest(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    views: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationResponse(BaseModel):
    id: int
    content_id: str
    region: str
    category: str
    content_type_id: str | None = None
    title: str
    address: str | None = None
    address_detail: str | None = None
    zipcode: str | None = None
    telephone: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    copyright_type: str | None = None
    created_time: str | None = None
    modified_time: str | None = None

    model_config = ConfigDict(from_attributes=True)
