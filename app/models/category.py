from datetime import datetime, timezone
from sqlalchemy import func
from sqlmodel import SQLModel, Field


class Category(SQLModel, table=True):
  id: int = Field(default=None, primary_key=True)
  name: str = Field(index=True, unique=True) 
  description: str | None = None
  created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column_kwargs={"server_default": func.now()})
  updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()})
