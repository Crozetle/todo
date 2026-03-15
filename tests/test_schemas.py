from datetime import datetime, timezone

from app.models import TodoStatus
from app.schemas import TodoCreate, TodoResponse, TodoStatusUpdate, TodoUpdate, UserCreate


def test_user_create_schema():
    u = UserCreate(username="alice", password="secret")
    assert u.username == "alice"
    assert u.password == "secret"


def test_todo_create_schema_defaults():
    t = TodoCreate(title="Buy milk")
    assert t.title == "Buy milk"
    assert t.description is None
    assert t.deadline is None


def test_todo_status_update_valid():
    s = TodoStatusUpdate(status=TodoStatus.done)
    assert s.status == TodoStatus.done


def test_todo_update_schema():
    t = TodoUpdate(title="Updated", description="New desc")
    assert t.title == "Updated"
    assert t.description == "New desc"
