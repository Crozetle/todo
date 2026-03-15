from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Todo, TodoStatus
from app.repositories.todos import (
    create_todo,
    delete_todo,
    get_todo_by_id,
    get_todos_by_user,
    update_todo,
    update_todo_status,
)

# Valid forward-only transitions
ALLOWED_TRANSITIONS: dict[TodoStatus, TodoStatus] = {
    TodoStatus.active: TodoStatus.done,
    TodoStatus.done: TodoStatus.archived,
}


def list_todos(db: Session, user_id: int, status: TodoStatus | None) -> list[Todo]:
    return get_todos_by_user(db, user_id, status)


def get_todo_or_404(db: Session, todo_id: int, user_id: int) -> Todo:
    todo = get_todo_by_id(db, todo_id, user_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


def create_new_todo(
    db: Session,
    user_id: int,
    title: str,
    description: str | None,
    deadline: datetime | None,
) -> Todo:
    return create_todo(db, user_id, title, description, deadline)


def edit_todo(
    db: Session,
    todo_id: int,
    user_id: int,
    title: str,
    description: str | None,
    deadline: datetime | None,
) -> Todo:
    todo = get_todo_or_404(db, todo_id, user_id)
    return update_todo(db, todo, title, description, deadline)


def transition_status(db: Session, todo_id: int, user_id: int, new_status: TodoStatus) -> Todo:
    todo = get_todo_or_404(db, todo_id, user_id)
    allowed = ALLOWED_TRANSITIONS.get(todo.status)
    if allowed != new_status:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot transition from '{todo.status}' to '{new_status}'",
        )
    return update_todo_status(db, todo, new_status)


def remove_todo(db: Session, todo_id: int, user_id: int) -> None:
    todo = get_todo_or_404(db, todo_id, user_id)
    delete_todo(db, todo)
