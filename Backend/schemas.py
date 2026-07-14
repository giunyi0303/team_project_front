from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    password: str = Field(min_length=1, max_length=100)


class PostUpdate(PostCreate):
    pass


class PasswordRequest(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
