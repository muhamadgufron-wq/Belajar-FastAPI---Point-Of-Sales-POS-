import uuid

from sqlmodel import SQLModel


class UserCreate(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    id: uuid.UUID
    username: str
    is_active: bool


class Token(SQLModel):
    access_token: str
    token_type: str
