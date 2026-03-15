from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Todo, TodoStatus


def get_todos_by_user(db: Session, user_id: int, status: TodoStatus | None = None) -> list[Todo]:
    q = db.query(Todo).filter(Todo.user_id == user_id)
    if status:
        q = q.filter(Todo.status == status)
    return q.order_by(Todo.created_at.desc()).all()


def get_todo_by_id(db: Session, todo_id: int, user_id: int) -> Todo | None:
    return db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == user_id).first()


def create_todo(
    db: Session,
    user_id: int,
    title: str,
    description: str | None,
    deadline: datetime | None,
) -> Todo:
    todo = Todo(user_id=user_id, title=title, description=description, deadline=deadline)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def update_todo(
    db: Session,
    todo: Todo,
    title: str,
    description: str | None,
    deadline: datetime | None,
) -> Todo:
    todo.title = title
    todo.description = description
    todo.deadline = deadline
    db.commit()
    db.refresh(todo)
    return todo


def update_todo_status(db: Session, todo: Todo, status: TodoStatus) -> Todo:
    todo.status = status
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo: Todo) -> None:
    db.delete(todo)
    db.commit()
