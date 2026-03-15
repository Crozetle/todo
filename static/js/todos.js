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
    // Switch to active tab so the new todo is visible
    currentStatus = 'active';
    document.querySelectorAll('#statusTabs .nav-link').forEach(b => {
      b.classList.toggle('active', b.dataset.status === 'active');
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
