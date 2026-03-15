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
