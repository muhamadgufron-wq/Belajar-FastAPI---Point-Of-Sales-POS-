import uuid

from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Username minimal 3 karakter dan maksimal 50 karakter",
    )
    password: str = Field(
        min_length=6,
        description="Password minimal 6 karakter demi keamanan",
    )
    role: str = Field(
        default="KASIR",
        description="Role pengguna: 'KASIR' atau 'OWNER'",
    )


class UserRead(SQLModel):
    id: uuid.UUID
    username: str
    role: str
    is_active: bool


class Token(SQLModel):
    access_token: str
    token_type: str
