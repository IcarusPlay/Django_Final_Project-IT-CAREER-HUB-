const API = 'http://127.0.0.1:8000/api';
const MEDIA_BASE = 'http://127.0.0.1:8000';

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

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

async function requestMultipart(url, method, formData) {
    const opts = {
        method,
        headers: { 'X-CSRFToken': getCookie('csrftoken') || '' },
        credentials: 'include',
        body: formData,
    };
    const res = await fetch(url, opts);
    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw json;
    return json;
}

// раньше в каждом catch(e) была своя логика вытаскивания текста ошибки, из-за чего
// иногда показывался только generic "Ошибка" вместо реальной причины
// (например DRF возвращает ошибку просто списком строк - ["Выбранные даты уже заняты"],
// а старый код проверял только e.non_field_errors/e.detail и не понимал такой формат)
function extractErrorMessage(e, fallback = 'Произошла ошибка') {
    if (!e) return fallback;
    if (Array.isArray(e)) return e[0] || fallback;
    if (typeof e === 'string') return e;
    if (e.detail) return e.detail;
    if (e.non_field_errors?.[0]) return e.non_field_errors[0];
    // объект вида {field: ["ошибка"]}  - берём первое попавшееся поле
    const firstKey = Object.keys(e)[0];
    if (firstKey) {
        const val = e[firstKey];
        return Array.isArray(val) ? val[0] : val;
    }
    return fallback;
}

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

function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}

function updateNav() {
    const user = getUser();
    const navLinks = document.getElementById('nav-links');
    if (!navLinks) return;

    if (user) {
        const bookingsLink = user.role === 'landlord'
            ? '<a href="/bookings/" style="position:relative;">Заявки на аренду<span id="incoming-badge" style="display:none; position:absolute; top:-8px; right:-14px; background:#e74c3c; color:#fff; font-size:11px; font-weight:700; border-radius:10px; padding:1px 6px;"></span></a>'
            : '<a href="/bookings/" style="position:relative;">Мои бронирования<span id="notif-badge" style="display:none; position:absolute; top:-8px; right:-14px; background:#e74c3c; color:#fff; font-size:11px; font-weight:700; border-radius:10px; padding:1px 6px;"></span></a>';

        navLinks.innerHTML = `
            <a href="/listings/">Объявления</a>
            ${user.role === 'landlord' ? '<a href="/listings/create/">+ Добавить</a>' : ''}
            ${user.role === 'landlord' ? '<a href="/listings/my/">Мои объявления</a>' : ''}
            ${bookingsLink}
            <div class="user-menu">
                <div class="user-avatar" onclick="toggleDropdown()">${user.username[0].toUpperCase()}</div>
                <div class="user-dropdown" id="user-dropdown">
                    <a href="#" style="cursor:default; color:#888;">${user.email}</a>
                    <hr>
                    <a href="/account/">Настройки аккаунта</a>
                    <a href="#" onclick="logout()">Выйти</a>
                </div>
            </div>
        `;

        if (user.role === 'landlord') {
            updateIncomingBadge();
        } else {
            updateNotifBadge();
        }
    } else {
        navLinks.innerHTML = `
            <a href="/listings/">Объявления</a>
            <a href="/auth/" class="btn btn-outline">Войти</a>
            <a href="/auth/?tab=register" class="btn btn-primary">Регистрация</a>
        `;
    }
}

// цифра над "Заявки на аренду" (арендодатель)
async function updateIncomingBadge() {
    try {
        const data = await request(`${API}/bookings/incoming-count/`);
        const badge = document.getElementById('incoming-badge');
        if (!badge) return;
        if (data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    } catch (e) {}
}

// пункт 2: цифра над "Мои бронирования" (арендатор) - сколько заявок изменили статус
// и он их ещё не видел; плюс всплывающее уведомление
async function updateNotifBadge() {
    try {
        const data = await request(`${API}/bookings/notifications-count/`);
        const badge = document.getElementById('notif-badge');
        if (data.count > 0) {
            if (badge) {
                badge.textContent = data.count;
                badge.style.display = 'inline-block';
            }
            toast(`У вас ${data.count} новых уведомлений о бронировании`, 'success');
        }
    } catch (e) {}
}

// вызывается на странице /bookings/ чтобы отметить уведомления просмотренными
async function markNotificationsSeen() {
    try {
        await request(`${API}/bookings/notifications-count/`, 'POST');
        const badge = document.getElementById('notif-badge');
        if (badge) badge.style.display = 'none';
    } catch (e) {}
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

function propertyIcon(type) {
    const icons = { apartment: '🏢', house: '🏠', room: '🛏️', studio: '🏙️' };
    return icons[type] || '🏠';
}

function listingImageHtml(listing) {
    if (listing.image) {
        const src = listing.image.startsWith('http') ? listing.image : `${MEDIA_BASE}${listing.image}`;
        return `<img src="${src}" alt="${listing.title}" style="width:100%; height:100%; object-fit:cover;">`;
    }
    return propertyIcon(listing.property_type);
}

function bookedBadgeHtml(listing) {
    if (listing.is_booked) {
        return '<span class="badge" style="background:#e74c3c22; color:#e74c3c; font-weight:600;">Забронировано</span>';
    }
    return '';
}

function stars(n) {
    return '★'.repeat(n) + '☆'.repeat(5 - n);
}

async function populateCitySelect(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;
    try {
        const cities = await request(`${API}/listings/cities/`);
        cities.forEach(city => {
            const exists = Array.from(select.options).some(o => o.value === city);
            if (!exists) {
                const opt = document.createElement('option');
                opt.value = city;
                opt.textContent = city;
                select.appendChild(opt);
            }
        });
    } catch (e) {}
}

// пункт 3: проверка пересечения с уже занятыми датами ДО отправки запроса на сервер -
// пользователь сразу видит понятную причину, а не только generic ошибку после клика
function datesOverlap(fromA, toA, fromB, toB) {
    return fromA < toB && fromB < toA;
}

async function checkDatesAvailable(listingId, dateFrom, dateTo) {
    try {
        const ranges = await request(`${API}/bookings/listing/${listingId}/booked-ranges/`);
        const conflict = ranges.some(r => datesOverlap(dateFrom, dateTo, r.date_from, r.date_to));
        return !conflict;
    } catch (e) {
        return true; // если проверка не удалась - не блокируем, сервер всё равно проверит
    }
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-menu')) {
        document.getElementById('user-dropdown')?.classList.remove('show');
    }
});
