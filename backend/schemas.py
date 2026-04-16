from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AuthRegisterRequest(BaseModel):
    model_config = ConfigDict(extra='ignore', populate_by_name=True)

    username: str
    email: str
    password: str
    confirm_password: str = Field(alias='confirmPassword')


class AuthLoginRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')

    email: str
    password: str


class BlogPostCreateRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)