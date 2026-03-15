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
