# Todo App Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a demo todo-list web app with registration, login, and full CRUD for tasks with status workflow (active → done → archived).

**Architecture:** Layered FastAPI backend (routes → services → repositories) serving a JSON REST API with Basic Auth. Frontend is multiple static HTML pages using Bootstrap + vanilla JS fetch calls.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, SQLite, Pydantic v2, passlib[bcrypt], pytest, httpx. Frontend: Bootstrap 5 CDN, vanilla JS.

---

## Task 1: Project scaffold and dependencies

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `app/__init__.py`
- Create: `app/routes/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/repositories/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.36
alembic==1.13.3
pydantic[email]==2.9.2
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
```

**Step 2: Create `requirements-dev.txt`**

```
pytest==8.3.3
httpx==0.27.2
pytest-asyncio==0.24.0
```

**Step 3: Create all `__init__.py` files (empty)**

```bash
mkdir -p app/routes app/services app/repositories tests static/pages static/js static/css
touch app/__init__.py app/routes/__init__.py app/services/__init__.py app/repositories/__init__.py tests/__init__.py
```

**Step 4: Install dependencies**

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

**Step 5: Commit**

```bash
git add requirements.txt requirements-dev.txt app/ tests/
git commit -m "chore: scaffold project structure and dependencies"
```

---

## Task 2: Database setup and ORM models

**Files:**
- Create: `app/database.py`
- Create: `app/models.py`

**Step 1: Create `app/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
```

**Step 2: Create `app/models.py`**

```python
import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TodoStatus(str, enum.Enum):
    active = "active"
    done = "done"
    archived = "archived"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    todos: Mapped[list["Todo"]] = relationship("Todo", back_populates="owner", cascade="all, delete-orphan")


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TodoStatus] = mapped_column(
        Enum(TodoStatus), default=TodoStatus.active, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="todos")
```

**Step 3: Write test to verify models import cleanly**

Create `tests/test_models.py`:

```python
from app.models import Todo, TodoStatus, User


def test_todo_status_values():
    assert TodoStatus.active == "active"
    assert TodoStatus.done == "done"
    assert TodoStatus.archived == "archived"


def test_user_model_tablename():
    assert User.__tablename__ == "users"


def test_todo_model_tablename():
    assert Todo.__tablename__ == "todos"
```

**Step 4: Run tests**

```bash
pytest tests/test_models.py -v
```
Expected: 3 PASSED

**Step 5: Commit**

```bash
git add app/database.py app/models.py tests/test_models.py
git commit -m "feat: add database setup and ORM models"
```

---

## Task 3: Alembic setup and initial migration

**Files:**
- Create: `alembic.ini` (generated)
- Create: `alembic/env.py` (modified)
- Create: `alembic/versions/<hash>_initial.py` (generated)

**Step 1: Initialize Alembic**

```bash
alembic init alembic
```

**Step 2: Edit `alembic/env.py`**

Replace the `target_metadata = None` line and add imports at the top:

```python
# At the top of env.py, after existing imports:
from app.database import Base, SQLALCHEMY_DATABASE_URL
from app import models  # noqa: F401 — ensures models are registered

# Replace:
# target_metadata = None
# With:
target_metadata = Base.metadata
```

Also update the `run_migrations_offline` function — replace the `url = config.get_main_option("sqlalchemy.url")` line:

```python
url = SQLALCHEMY_DATABASE_URL
```

And update `run_migrations_online` — replace the `connectable = engine_from_config(...)` block:

```python
from app.database import engine as connectable
```

**Step 3: Edit `alembic.ini` — set sqlalchemy.url**

Find the line `sqlalchemy.url = driver://user:pass@localhost/dbname` and replace:

```ini
sqlalchemy.url = sqlite:///./todo.db
```

**Step 4: Generate initial migration**

```bash
alembic revision --autogenerate -m "initial"
```
Expected: creates `alembic/versions/<hash>_initial.py` with CreateTable for users and todos.

**Step 5: Run migration**

```bash
alembic upgrade head
```
Expected: creates `todo.db` with users and todos tables.

**Step 6: Commit**

```bash
git add alembic/ alembic.ini
git commit -m "feat: add alembic setup and initial migration"
```

---

## Task 4: Pydantic schemas

**Files:**
- Create: `app/schemas.py`

**Step 1: Create `app/schemas.py`**

```python
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
```

**Step 2: Write schema tests**

Create `tests/test_schemas.py`:

```python
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
```

**Step 3: Run tests**

```bash
pytest tests/test_schemas.py -v
```
Expected: 4 PASSED

**Step 4: Commit**

```bash
git add app/schemas.py tests/test_schemas.py
git commit -m "feat: add pydantic schemas"
```

---

## Task 5: Dependencies (get_db, get_current_user)

**Files:**
- Create: `app/dependencies.py`

**Step 1: Create `app/dependencies.py`**

```python
import base64
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User

security = HTTPBasic()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    from app.services.auth import verify_password
    from app.repositories.users import get_user_by_username

    user = get_user_by_username(db, credentials.username)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user
```

**Step 2: Commit**

```bash
git add app/dependencies.py
git commit -m "feat: add FastAPI dependencies (get_db, get_current_user)"
```

---

## Task 6: User repository and auth service

**Files:**
- Create: `app/repositories/users.py`
- Create: `app/services/auth.py`

**Step 1: Create `app/repositories/users.py`**

```python
from sqlalchemy.orm import Session

from app.models import User


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, username: str, hashed_password: str) -> User:
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

**Step 2: Create `app/services/auth.py`**

```python
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.users import create_user, get_user_by_username

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def register_user(db: Session, username: str, password: str) -> User:
    existing = get_user_by_username(db, username)
    if existing:
        raise ValueError(f"Username '{username}' is already taken")
    hashed = hash_password(password)
    return create_user(db, username, hashed)
```

**Step 3: Write tests**

Create `tests/test_auth_service.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.auth import hash_password, register_user, verify_password


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert verify_password("mysecret", hashed)
    assert not verify_password("wrong", hashed)


def test_register_user_success(db):
    user = register_user(db, "alice", "password123")
    assert user.id is not None
    assert user.username == "alice"
    assert user.hashed_password != "password123"


def test_register_user_duplicate_raises(db):
    register_user(db, "alice", "password123")
    with pytest.raises(ValueError, match="already taken"):
        register_user(db, "alice", "otherpassword")
```

**Step 4: Run tests**

```bash
pytest tests/test_auth_service.py -v
```
Expected: 3 PASSED

**Step 5: Commit**

```bash
git add app/repositories/users.py app/services/auth.py tests/test_auth_service.py
git commit -m "feat: add user repository and auth service"
```

---

## Task 7: Todo repository and todo service

**Files:**
- Create: `app/repositories/todos.py`
- Create: `app/services/todos.py`

**Step 1: Create `app/repositories/todos.py`**

```python
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
```

**Step 2: Create `app/services/todos.py`**

```python
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
```

**Step 3: Write tests**

Create `tests/test_todo_service.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import TodoStatus
from app.services.auth import register_user
from app.services.todos import (
    create_new_todo,
    get_todo_or_404,
    list_todos,
    remove_todo,
    transition_status,
    edit_todo,
)
from fastapi import HTTPException


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
```

**Step 4: Run tests**

```bash
pytest tests/test_todo_service.py -v
```
Expected: 7 PASSED

**Step 5: Commit**

```bash
git add app/repositories/todos.py app/services/todos.py tests/test_todo_service.py
git commit -m "feat: add todo repository and service with status transitions"
```

---

## Task 8: Auth routes

**Files:**
- Create: `app/routes/auth.py`

**Step 1: Create `app/routes/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.services.auth import register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = register_user(db, payload.username, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return user


@router.post("/login", response_model=UserResponse)
def login(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # Stateless: client clears sessionStorage
    return None
```

**Step 2: Commit**

```bash
git add app/routes/auth.py
git commit -m "feat: add auth routes (register, login, logout)"
```

---

## Task 9: Todo routes

**Files:**
- Create: `app/routes/todos.py`

**Step 1: Create `app/routes/todos.py`**

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Todo, TodoStatus, User
from app.schemas import TodoCreate, TodoResponse, TodoStatusUpdate, TodoUpdate
from app.services.todos import (
    create_new_todo,
    get_todo_or_404,
    list_todos,
    remove_todo,
    transition_status,
    edit_todo,
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
```

**Step 2: Commit**

```bash
git add app/routes/todos.py
git commit -m "feat: add todo CRUD routes"
```

---

## Task 10: Main FastAPI app assembly

**Files:**
- Create: `main.py`

**Step 1: Create `main.py`**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.routes import auth, todos

app = FastAPI(title="Todo App")

app.include_router(auth.router)
app.include_router(todos.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/pages/login.html")
```

**Step 2: Write integration tests**

Create `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.dependencies import get_db
from main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
```

Create `tests/test_api.py`:

```python
import base64


def auth_header(username: str, password: str) -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_register(client):
    r = client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    assert r.status_code == 201
    assert r.json()["username"] == "alice"


def test_register_duplicate_returns_409(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    r = client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    assert r.status_code == 409


def test_login_success(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    r = client.post("/api/auth/login", headers=auth_header("alice", "pass"))
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    r = client.post("/api/auth/login", headers=auth_header("alice", "wrong"))
    assert r.status_code == 401


def test_create_and_list_todos(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    headers = auth_header("alice", "pass")
    r = client.post("/api/todos/", json={"title": "Buy milk"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["status"] == "active"

    r = client.get("/api/todos/", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_status_transition(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    headers = auth_header("alice", "pass")
    todo = client.post("/api/todos/", json={"title": "Task"}, headers=headers).json()

    r = client.patch(f"/api/todos/{todo['id']}/status", json={"status": "done"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "done"

    r = client.patch(f"/api/todos/{todo['id']}/status", json={"status": "archived"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "archived"


def test_invalid_status_transition(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    headers = auth_header("alice", "pass")
    todo = client.post("/api/todos/", json={"title": "Task"}, headers=headers).json()
    r = client.patch(f"/api/todos/{todo['id']}/status", json={"status": "archived"}, headers=headers)
    assert r.status_code == 422


def test_delete_todo(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    headers = auth_header("alice", "pass")
    todo = client.post("/api/todos/", json={"title": "Task"}, headers=headers).json()
    r = client.delete(f"/api/todos/{todo['id']}", headers=headers)
    assert r.status_code == 204

    r = client.get("/api/todos/", headers=headers)
    assert r.json() == []


def test_todo_isolation_between_users(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    client.post("/api/auth/register", json={"username": "bob", "password": "pass"})
    alice_h = auth_header("alice", "pass")
    bob_h = auth_header("bob", "pass")

    client.post("/api/todos/", json={"title": "Alice task"}, headers=alice_h)
    r = client.get("/api/todos/", headers=bob_h)
    assert r.json() == []
```

**Step 3: Run all tests**

```bash
pytest -v
```
Expected: all tests PASSED

**Step 4: Commit**

```bash
git add main.py tests/conftest.py tests/test_api.py
git commit -m "feat: assemble FastAPI app with integration tests"
```

---

## Task 11: Frontend — login.html and register.html

**Files:**
- Create: `static/pages/login.html`
- Create: `static/pages/register.html`
- Create: `static/js/auth.js`

**Step 1: Create `static/pages/login.html`**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Вход — Todo App</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body class="bg-light">
  <div class="container d-flex justify-content-center align-items-center min-vh-100">
    <div class="card shadow-sm" style="width: 100%; max-width: 400px;">
      <div class="card-body p-4">
        <h2 class="card-title text-center mb-4">Todo App</h2>
        <div id="error-msg" class="alert alert-danger d-none"></div>
        <form id="login-form">
          <div class="mb-3">
            <label for="username" class="form-label">Логин</label>
            <input type="text" class="form-control" id="username" required autocomplete="username">
          </div>
          <div class="mb-3">
            <label for="password" class="form-label">Пароль</label>
            <input type="password" class="form-control" id="password" required autocomplete="current-password">
          </div>
          <button type="submit" class="btn btn-primary w-100">Войти</button>
        </form>
        <hr>
        <p class="text-center mb-0">Нет аккаунта? <a href="/static/pages/register.html">Зарегистрироваться</a></p>
      </div>
    </div>
  </div>
  <script src="/static/js/auth.js"></script>
</body>
</html>
```

**Step 2: Create `static/pages/register.html`**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Регистрация — Todo App</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body class="bg-light">
  <div class="container d-flex justify-content-center align-items-center min-vh-100">
    <div class="card shadow-sm" style="width: 100%; max-width: 400px;">
      <div class="card-body p-4">
        <h2 class="card-title text-center mb-4">Регистрация</h2>
        <div id="error-msg" class="alert alert-danger d-none"></div>
        <div id="success-msg" class="alert alert-success d-none"></div>
        <form id="register-form">
          <div class="mb-3">
            <label for="username" class="form-label">Логин</label>
            <input type="text" class="form-control" id="username" required autocomplete="username">
          </div>
          <div class="mb-3">
            <label for="password" class="form-label">Пароль</label>
            <input type="password" class="form-control" id="password" required autocomplete="new-password">
          </div>
          <button type="submit" class="btn btn-success w-100">Зарегистрироваться</button>
        </form>
        <hr>
        <p class="text-center mb-0">Уже есть аккаунт? <a href="/static/pages/login.html">Войти</a></p>
      </div>
    </div>
  </div>
  <script src="/static/js/auth.js"></script>
</body>
</html>
```

**Step 3: Create `static/js/auth.js`**

```javascript
function makeBasicAuth(username, password) {
  return 'Basic ' + btoa(username + ':' + password);
}

function showError(msg) {
  const el = document.getElementById('error-msg');
  el.textContent = msg;
  el.classList.remove('d-none');
}

function hideError() {
  document.getElementById('error-msg')?.classList.add('d-none');
}

// LOGIN
const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Authorization': makeBasicAuth(username, password) }
    });

    if (res.ok) {
      sessionStorage.setItem('username', username);
      sessionStorage.setItem('password', password);
      window.location.href = '/static/pages/todos.html';
    } else {
      showError('Неверный логин или пароль');
    }
  });
}

// REGISTER
const registerForm = document.getElementById('register-form');
if (registerForm) {
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok) {
      const successEl = document.getElementById('success-msg');
      successEl.textContent = 'Аккаунт создан! Перенаправляем...';
      successEl.classList.remove('d-none');
      setTimeout(() => window.location.href = '/static/pages/login.html', 1500);
    } else {
      const data = await res.json();
      showError(data.detail || 'Ошибка регистрации');
    }
  });
}
```

**Step 4: Commit**

```bash
git add static/pages/login.html static/pages/register.html static/js/auth.js
git commit -m "feat: add login and register pages with auth JS"
```

---

## Task 12: Frontend — todos.html and todos.js

**Files:**
- Create: `static/pages/todos.html`
- Create: `static/js/todos.js`

**Step 1: Create `static/pages/todos.html`**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Мои задачи — Todo App</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
  <!-- Navbar -->
  <nav class="navbar navbar-dark bg-primary">
    <div class="container">
      <span class="navbar-brand mb-0 h1">Todo App</span>
      <div class="d-flex align-items-center gap-3">
        <span class="text-white" id="nav-username"></span>
        <button class="btn btn-outline-light btn-sm" id="logout-btn">Выйти</button>
      </div>
    </div>
  </nav>

  <div class="container mt-4">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h4 class="mb-0">Мои задачи</h4>
      <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#todoModal" id="create-btn">
        + Создать задачу
      </button>
    </div>

    <!-- Tabs -->
    <ul class="nav nav-tabs" id="statusTabs">
      <li class="nav-item">
        <button class="nav-link active" data-status="active">Активные</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-status="done">Выполненные</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-status="archived">Архив</button>
      </li>
    </ul>

    <!-- Todo list -->
    <div id="todo-list" class="mt-3">
      <div class="text-center text-muted py-5" id="empty-msg">Задач нет</div>
    </div>
  </div>

  <!-- Todo Modal (Create / Edit) -->
  <div class="modal fade" id="todoModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="modal-title">Новая задача</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form id="todo-form">
            <input type="hidden" id="todo-id">
            <div class="mb-3">
              <label for="todo-title" class="form-label">Название <span class="text-danger">*</span></label>
              <input type="text" class="form-control" id="todo-title" required>
            </div>
            <div class="mb-3">
              <label for="todo-description" class="form-label">Описание</label>
              <textarea class="form-control" id="todo-description" rows="3"></textarea>
            </div>
            <div class="mb-3">
              <label for="todo-deadline" class="form-label">Дедлайн</label>
              <input type="datetime-local" class="form-control" id="todo-deadline">
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
          <button type="button" class="btn btn-primary" id="modal-submit">Сохранить</button>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="/static/js/todos.js"></script>
</body>
</html>
```

**Step 2: Create `static/js/todos.js`**

```javascript
// --- Auth helpers ---
const username = sessionStorage.getItem('username');
const password = sessionStorage.getItem('password');

if (!username || !password) {
  window.location.href = '/static/pages/login.html';
}

document.getElementById('nav-username').textContent = username;

function authHeaders() {
  return {
    'Authorization': 'Basic ' + btoa(username + ':' + password),
    'Content-Type': 'application/json',
  };
}

// --- Logout ---
document.getElementById('logout-btn').addEventListener('click', async () => {
  await fetch('/api/auth/logout', { method: 'POST', headers: authHeaders() });
  sessionStorage.clear();
  window.location.href = '/static/pages/login.html';
});

// --- State ---
let currentStatus = 'active';

// --- Tab switching ---
document.querySelectorAll('#statusTabs .nav-link').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#statusTabs .nav-link').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentStatus = btn.dataset.status;
    loadTodos();
  });
});

// --- Load todos ---
async function loadTodos() {
  const res = await fetch(`/api/todos/?status=${currentStatus}`, { headers: authHeaders() });
  if (!res.ok) return;
  const todos = await res.json();
  renderTodos(todos);
}

function formatDeadline(deadline) {
  if (!deadline) return '';
  const d = new Date(deadline);
  const now = new Date();
  const overdue = d < now;
  const str = d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  return `<span class="badge ${overdue ? 'bg-danger' : 'bg-secondary'}">${str}</span>`;
}

function renderTodos(todos) {
  const list = document.getElementById('todo-list');
  const emptyMsg = document.getElementById('empty-msg');

  if (todos.length === 0) {
    list.innerHTML = '';
    emptyMsg.style.display = 'block';
    return;
  }
  emptyMsg.style.display = 'none';

  list.innerHTML = todos.map(todo => `
    <div class="card mb-2 todo-card" id="todo-${todo.id}">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <h6 class="card-title mb-1">${escapeHtml(todo.title)}</h6>
            ${todo.description ? `<p class="card-text text-muted small mb-1">${escapeHtml(todo.description)}</p>` : ''}
            ${formatDeadline(todo.deadline)}
          </div>
          <div class="d-flex gap-1 ms-2 flex-shrink-0">
            ${renderButtons(todo)}
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

function renderButtons(todo) {
  const buttons = [];
  if (todo.status === 'active') {
    buttons.push(`<button class="btn btn-sm btn-outline-secondary" onclick="openEdit(${todo.id})">Изменить</button>`);
    buttons.push(`<button class="btn btn-sm btn-success" onclick="changeStatus(${todo.id}, 'done')">Выполнить</button>`);
  }
  if (todo.status === 'done') {
    buttons.push(`<button class="btn btn-sm btn-outline-secondary" onclick="changeStatus(${todo.id}, 'archived')">Архивировать</button>`);
  }
  buttons.push(`<button class="btn btn-sm btn-outline-danger" onclick="deleteTodo(${todo.id})">Удалить</button>`);
  return buttons.join('');
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// --- Create / Edit modal ---
const todoModal = new bootstrap.Modal(document.getElementById('todoModal'));

document.getElementById('create-btn').addEventListener('click', () => {
  document.getElementById('modal-title').textContent = 'Новая задача';
  document.getElementById('todo-id').value = '';
  document.getElementById('todo-title').value = '';
  document.getElementById('todo-description').value = '';
  document.getElementById('todo-deadline').value = '';
});

async function openEdit(id) {
  const res = await fetch(`/api/todos/${id}`, { headers: authHeaders() });
  if (!res.ok) return;
  const todo = await res.json();

  document.getElementById('modal-title').textContent = 'Редактировать задачу';
  document.getElementById('todo-id').value = todo.id;
  document.getElementById('todo-title').value = todo.title;
  document.getElementById('todo-description').value = todo.description || '';
  document.getElementById('todo-deadline').value = todo.deadline
    ? new Date(todo.deadline).toISOString().slice(0, 16)
    : '';
  todoModal.show();
}

document.getElementById('modal-submit').addEventListener('click', async () => {
  const id = document.getElementById('todo-id').value;
  const title = document.getElementById('todo-title').value.trim();
  const description = document.getElementById('todo-description').value.trim() || null;
  const deadlineRaw = document.getElementById('todo-deadline').value;
  const deadline = deadlineRaw ? new Date(deadlineRaw).toISOString() : null;

  if (!title) return;

  const payload = { title, description, deadline };

  if (id) {
    await fetch(`/api/todos/${id}`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
  } else {
    await fetch('/api/todos/', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
  }

  todoModal.hide();
  loadTodos();
});

// --- Status change ---
async function changeStatus(id, status) {
  await fetch(`/api/todos/${id}/status`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify({ status }),
  });
  loadTodos();
}

// --- Delete ---
async function deleteTodo(id) {
  if (!confirm('Удалить задачу?')) return;
  await fetch(`/api/todos/${id}`, { method: 'DELETE', headers: authHeaders() });
  loadTodos();
}

// --- Init ---
loadTodos();
```

**Step 3: Commit**

```bash
git add static/pages/todos.html static/js/todos.js
git commit -m "feat: add todos page with tabs, modal, and full CRUD JS"
```

---

## Task 13: CSS styles

**Files:**
- Create: `static/css/styles.css`

**Step 1: Create `static/css/styles.css`**

```css
body {
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.todo-card {
  transition: box-shadow 0.15s ease;
}

.todo-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-tabs .nav-link {
  cursor: pointer;
}

#empty-msg {
  font-size: 1.1rem;
}
```

**Step 2: Commit**

```bash
git add static/css/styles.css
git commit -m "feat: add base CSS styles"
```

---

## Task 14: Manual smoke test

**Step 1: Start the server**

```bash
uvicorn main:app --reload
```

**Step 2: Open browser and verify**

1. Go to `http://localhost:8000` → redirects to login page
2. Click "Зарегистрироваться" → register a user
3. Login → redirected to todos page
4. Create a todo with title, description, deadline
5. Mark as done → card moves to "Выполненные" tab
6. Archive → card moves to "Архив" tab
7. Delete a todo
8. Logout → redirected to login

**Step 3: Run full test suite one last time**

```bash
pytest -v
```
Expected: all tests PASSED

**Step 4: Final commit if any loose files**

```bash
git status
# commit anything remaining
```

---

## Summary

| Task | What it builds |
|------|---------------|
| 1 | Project scaffold + deps |
| 2 | SQLAlchemy models |
| 3 | Alembic migrations |
| 4 | Pydantic schemas |
| 5 | FastAPI dependencies |
| 6 | User repo + auth service |
| 7 | Todo repo + todo service |
| 8 | Auth routes |
| 9 | Todo routes |
| 10 | App assembly + integration tests |
| 11 | Login + Register pages |
| 12 | Todos page + JS |
| 13 | CSS styles |
| 14 | Smoke test |
