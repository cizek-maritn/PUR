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