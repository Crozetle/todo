# Todo App — Design Document

**Date:** 2026-03-15
**Stack:** FastAPI, SQLite, Pydantic, Alembic, Bootstrap, vanilla JS

---

## Overview

Demo todo-list web application with user authentication, full CRUD for tasks, and a status-based workflow. Frontend is a multi-page SPA communicating with a FastAPI JSON REST API via fetch requests and Basic Auth.

---

## Architecture

**Approach:** Layered (routes → services → repositories)

- `routes/` — HTTP handlers, request/response validation
- `services/` — business logic (password hashing, status transitions)
- `repositories/` — database queries (SQLAlchemy)
- `models.py` — SQLAlchemy ORM models
- `schemas.py` — Pydantic request/response schemas
- `database.py` — SQLAlchemy engine and session
- `dependencies.py` — FastAPI dependencies (`get_db`, `get_current_user`)

---

## Project Structure

```
todo/
├── alembic/
│   └── versions/
├── app/
│   ├── routes/
│   │   ├── auth.py
│   │   └── todos.py
│   ├── services/
│   │   ├── auth.py
│   │   └── todos.py
│   ├── repositories/
│   │   ├── users.py
│   │   └── todos.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── dependencies.py
├── static/
│   ├── pages/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── todos.html
│   ├── js/
│   │   ├── auth.js
│   │   └── todos.js
│   └── css/
│       └── styles.css
├── main.py
├── alembic.ini
└── requirements.txt
```

---

## Data Models

### User
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | |
| `username` | String, unique | login |
| `hashed_password` | String | bcrypt via passlib |

### Todo
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | |
| `user_id` | Integer FK → User | owner |
| `title` | String | required |
| `description` | Text, nullable | optional |
| `status` | Enum | `active` / `done` / `archived` |
| `created_at` | DateTime | auto on insert |
| `deadline` | DateTime, nullable | optional |

---

## API Endpoints

### Auth — `/api/auth`
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/register` | Register, body: `{username, password}` |
| `POST` | `/login` | Login via Basic Auth header, returns `{username}` |
| `POST` | `/logout` | Logout (client clears sessionStorage) |

### Todos — `/api/todos` (all protected by Basic Auth)
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List todos, filter `?status=active\|done\|archived` |
| `POST` | `/` | Create todo |
| `GET` | `/{id}` | Get single todo |
| `PUT` | `/{id}` | Edit title, description, deadline |
| `PATCH` | `/{id}/status` | Transition status |
| `DELETE` | `/{id}` | Delete todo |

---

## Authentication

- **Mechanism:** HTTP Basic Auth
- Client encodes `username:password` as Base64 and sends `Authorization: Basic <token>` on every request
- Credentials stored in `sessionStorage` after login
- FastAPI Dependency `get_current_user` decodes header, looks up user, verifies bcrypt hash
- Logout clears `sessionStorage` and redirects to `login.html`

---

## Status Workflow

```
active → done → archived
```

- Only forward transitions allowed
- `active`: can Edit, Mark Done, Delete
- `done`: can Archive, Delete
- `archived`: can only Delete

---

## Frontend

### Pages
- `login.html` — login form, link to register
- `register.html` — register form, link to login
- `todos.html` — main app (redirects to login if not authenticated)

### todos.html Layout
- **Navbar:** username + Logout button
- **Header:** "Create Task" button → Bootstrap Modal with form
- **Bootstrap Tabs:** Active / Done / Archive
- **Todo card fields:** title, description (collapsed), deadline, action buttons

### JS Behavior
- On page load: check `sessionStorage` for credentials, if missing → redirect to `login.html`
- All API calls attach `Authorization: Basic <base64>` header
- Tab switch triggers filtered GET request
- Modal used for both Create and Edit (reused with different submit handler)
