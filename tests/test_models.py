from app.models import Todo, TodoStatus, User


def test_todo_status_values():
    assert TodoStatus.active == "active"
    assert TodoStatus.done == "done"
    assert TodoStatus.archived == "archived"


def test_user_model_tablename():
    assert User.__tablename__ == "users"


def test_todo_model_tablename():
    assert Todo.__tablename__ == "todos"
