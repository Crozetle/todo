import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import TodoStatus
from app.services.auth import register_user
from app.services.todos import (
    create_new_todo,
    edit_todo,
    get_todo_or_404,
    list_todos,
    remove_todo,
    transition_status,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def user(db):
    return register_user(db, "alice", "pass")


def test_create_and_list_todo(db, user):
    todo = create_new_todo(db, user.id, "Buy milk", None, None)
    assert todo.id is not None
    assert todo.status == TodoStatus.active

    todos = list_todos(db, user.id, None)
    assert len(todos) == 1
    assert todos[0].title == "Buy milk"


def test_get_todo_or_404_not_found(db, user):
    with pytest.raises(HTTPException) as exc_info:
        get_todo_or_404(db, 999, user.id)
    assert exc_info.value.status_code == 404


def test_transition_active_to_done(db, user):
    todo = create_new_todo(db, user.id, "Task", None, None)
    updated = transition_status(db, todo.id, user.id, TodoStatus.done)
    assert updated.status == TodoStatus.done


def test_transition_done_to_archived(db, user):
    todo = create_new_todo(db, user.id, "Task", None, None)
    transition_status(db, todo.id, user.id, TodoStatus.done)
    updated = transition_status(db, todo.id, user.id, TodoStatus.archived)
    assert updated.status == TodoStatus.archived


def test_invalid_transition_raises(db, user):
    todo = create_new_todo(db, user.id, "Task", None, None)
    with pytest.raises(HTTPException) as exc_info:
        transition_status(db, todo.id, user.id, TodoStatus.archived)
    assert exc_info.value.status_code == 422


def test_remove_todo(db, user):
    todo = create_new_todo(db, user.id, "Task", None, None)
    remove_todo(db, todo.id, user.id)
    assert list_todos(db, user.id, None) == []


def test_edit_todo(db, user):
    todo = create_new_todo(db, user.id, "Old title", None, None)
    updated = edit_todo(db, todo.id, user.id, "New title", "desc", None)
    assert updated.title == "New title"
    assert updated.description == "desc"
