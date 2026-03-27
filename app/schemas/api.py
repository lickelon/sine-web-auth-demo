from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SignupRequest(BaseModel):
    username: str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    username: str
    password: str


class MessageResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    created_at: datetime


class ProfileResponse(BaseModel):
    message: str
    user: UserResponse
