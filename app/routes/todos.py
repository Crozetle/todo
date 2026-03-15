from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import TodoStatus, User
from app.schemas import TodoCreate, TodoResponse, TodoStatusUpdate, TodoUpdate
from app.services.todos import (
    create_new_todo,
    edit_todo,
    get_todo_or_404,
    list_todos,
    remove_todo,
    transition_status,
)

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("/", response_model=list[TodoResponse])
def get_todos(
    status: TodoStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_todos(db, current_user.id, status)


@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    payload: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_new_todo(db, current_user.id, payload.title, payload.description, payload.deadline)


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_todo_or_404(db, todo_id, current_user.id)


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return edit_todo(db, todo_id, current_user.id, payload.title, payload.description, payload.deadline)


@router.patch("/{todo_id}/status", response_model=TodoResponse)
def patch_todo_status(
    todo_id: int,
    payload: TodoStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transition_status(db, todo_id, current_user.id, payload.status)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    remove_todo(db, todo_id, current_user.id)
