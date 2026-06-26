const API = 'http://127.0.0.1:8000/api';

// получаем csrftoken из куки
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// базовый fetch с csrf
async function request(url, method = 'GET', data = null) {
    const opts = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || '',
        },
        credentials: 'include',
    };
    if (data) opts.body = JSON.stringify(data);

    const res = await fetch(url, opts);
    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw json;
    return json;
}

// показать тост уведомление
function toast(msg, type = '') {
    let el = document.getElementById('toast');
    if (!el) {
        el = document.createElement('div');
        el.id = 'toast';
        el.className = 'toast';
        document.body.appendChild(el);
    }
    el.textContent = msg;
    el.className = `toast ${type} show`;
    setTimeout(() => el.classList.remove('show'), 3000);
}

// текущий пользователь из localStorage
function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}

// обновить навбар в зависимости от авторизации
function updateNav() {
    const user = getUser();
    const navLinks = document.getElementById('nav-links');
    if (!navLinks) return;

    if (user) {
        navLinks.innerHTML = `
            <a href="/listings/">Объявления</a>
            ${user.role === 'landlord' ? '<a href="/listings/create/">+ Добавить</a>' : ''}
            <a href="/bookings/">Мои бронирования</a>
            <div class="user-menu">
                <div class="user-avatar" onclick="toggleDropdown()">${user.username[0].toUpperCase()}</div>
                <div class="user-dropdown" id="user-dropdown">
                    <a href="/profile/">${user.email}</a>
                    <hr>
                    <a href="#" onclick="logout()">Выйти</a>
                </div>
            </div>
        `;
    } else {
        navLinks.innerHTML = `
            <a href="/listings/">Объявления</a>
            <a href="/auth/" class="btn btn-outline">Войти</a>
            <a href="/auth/?tab=register" class="btn btn-primary">Регистрация</a>
        `;
    }
}

function toggleDropdown() {
    document.getElementById('user-dropdown')?.classList.toggle('show');
}

async function logout() {
    try {
        await request(`${API}/auth/logout/`, 'POST');
    } catch(e) {}
    localStorage.removeItem('user');
    window.location.href = '/';
}

// тип жилья -> эмодзи
function propertyIcon(type) {
    const icons = { apartment: '🏢', house: '🏠', room: '🛏️', studio: '🏙️' };
    return icons[type] || '🏠';
}

// звёздочки для рейтинга
function stars(n) {
    return '★'.repeat(n) + '☆'.repeat(5 - n);
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-menu')) {
        document.getElementById('user-dropdown')?.classList.remove('show');
    }
});
