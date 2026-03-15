from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import TodoStatus


# --- Auth schemas ---

class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


# --- Todo schemas ---

class TodoCreate(BaseModel):
    title: str
    description: str | None = None
    deadline: datetime | None = None


class TodoUpdate(BaseModel):
    title: str
    description: str | None = None
    deadline: datetime | None = None


class TodoStatusUpdate(BaseModel):
    status: TodoStatus


class TodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TodoStatus
    created_at: datetime
    deadline: datetime | None
    user_id: int
