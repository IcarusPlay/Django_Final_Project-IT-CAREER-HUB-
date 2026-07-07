# Django Final Project - Livento API

Backend-приложение для платформы аренды жилья. Позволяет арендодателям размещать объявления, а арендаторам - искать жильё, бронировать его и оставлять отзывы.

---

## Технологии

- Python 3.12
- Django 6.0
- Django REST Framework
- MySQL
- Docker + Docker Compose
- drf-spectacular (Swagger)

---

## Установка и запуск

### Локально

**1. Клонировать репозиторий:**
```bash
git clone https://github.com/IcarusPlay/Django_Final_Project-IT-CAREER-HUB-.git
cd Django_Final_Project-IT-CAREER-HUB-
```

**2. Создать и активировать виртуальное окружение:**
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
```

**3. Установить зависимости:**
```bash
pip install -r requirements.txt
```

**4. Создать `.env` файл на основе примера:**
```bash
cp .env.example .env
```
Заполнить `.env` своими данными (SECRET_KEY, DB_NAME, DB_USER и т.д.)

**5. Настройка базы данных**

> Если у вас нет MySQL - можно быстро запустить через SQLite (встроена в Python, ничего устанавливать не нужно).
> Для этого в `config/settings.py` замените блок `DATABASES` на:
> ```python
> DATABASES = {
>     'default': {
>         'ENGINE': 'django.db.backends.sqlite3',
>         'NAME': BASE_DIR / 'db.sqlite3',
>     }
> }
> ```
> После этого можно сразу переходить к шагу 6.

Если используете MySQL - создайте базу данных:
```sql
CREATE DATABASE rental_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**6. Применить миграции:**
```bash
python manage.py migrate
```

**7. Запустить сервер:**
```bash
python manage.py runserver
```

---

### Через Docker

```bash
docker-compose up --build
```

---

## Swagger документация

После запуска сервера документация доступна по адресам:

- Swagger UI: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- ReDoc: [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)

---

## Структура проекта

```
Django_Final_Project/
├── apps/
│   ├── users/        # аутентификация, роли пользователей
│   ├── listings/     # объявления, поиск, фильтрация
│   ├── bookings/     # бронирования
│   └── reviews/      # отзывы и рейтинги
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── templates/        # HTML страницы фронтенда
├── static/           # CSS и JS файлы
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

Каждое приложение внутри разделено на слои:
- `models/` - модели базы данных
- `serializers/` - валидация и сериализация данных
- `repositories/` - запросы в базу данных
- `services/` - бизнес-логика
- `controllers/` - обработка HTTP запросов (views + urls)

---

## API Эндпоинты

### Аутентификация
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход |
| POST | `/api/auth/logout/` | Выход |
| GET | `/api/auth/me/` | Текущий пользователь |

### Объявления
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/listings/` | Список объявлений (с фильтрами) |
| POST | `/api/listings/` | Создать объявление |
| GET | `/api/listings/<id>/` | Детали объявления |
| PUT/PATCH | `/api/listings/<id>/` | Редактировать объявление |
| DELETE | `/api/listings/<id>/` | Удалить объявление (мягкое удаление) |
| POST | `/api/listings/<id>/toggle/` | Вкл/выкл видимость |
| GET | `/api/listings/my/` | Мои объявления |
| GET | `/api/listings/search-history/` | История поиска |
| GET | `/api/listings/popular-keywords/` | Популярные запросы |

### Фильтры для GET /api/listings/
| Параметр | Описание | Пример |
|----------|----------|--------|
| `search` | Поиск по названию и описанию | `?search=квартира` |
| `city` | Фильтр по городу | `?city=Berlin` |
| `district` | Фильтр по району | `?district=Mitte` |
| `property_type` | Тип жилья | `?property_type=apartment` |
| `rooms` | Точное кол-во комнат | `?rooms=2` |
| `rooms_min` | Минимум комнат | `?rooms_min=1` |
| `rooms_max` | Максимум комнат | `?rooms_max=3` |
| `price_min` | Минимальная цена | `?price_min=50` |
| `price_max` | Максимальная цена | `?price_max=200` |
| `ordering` | Сортировка | `?ordering=-price_per_night` |

### Бронирования
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/bookings/` | Мои бронирования |
| POST | `/api/bookings/` | Создать бронирование |
| GET | `/api/bookings/<id>/` | Детали бронирования |
| POST | `/api/bookings/<id>/cancel/` | Отменить |
| POST | `/api/bookings/<id>/confirm/` | Подтвердить (арендодатель) |
| POST | `/api/bookings/<id>/reject/` | Отклонить (арендодатель) |

### Отзывы
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/reviews/<listing_id>/reviews/` | Отзывы объявления |
| POST | `/api/reviews/<listing_id>/reviews/` | Оставить отзыв |
| DELETE | `/api/reviews/<listing_id>/reviews/<id>/` | Удалить отзыв |

---

## Роли пользователей

Роль реализована через `TextChoices` в модели `User`:

```python
class Role(models.TextChoices):
    LANDLORD = 'landlord', 'Landlord'
    TENANT = 'tenant', 'Tenant'
```

- **Tenant (арендатор)** - может просматривать объявления, создавать бронирования, оставлять отзывы
- **Landlord (арендодатель)** - может создавать и управлять своими объявлениями, подтверждать/отклонять бронирования

---

## Валидация данных

- **Телефон** - проверяется регулярным выражением, принимается международный формат (`+491234567890`, 8-15 цифр)
- **Цена за ночь** - не может быть меньше 1 (`MinValueValidator`)
- **Даты бронирования** - дата выезда должна быть позже даты заезда. Проверка на двух уровнях: в модели (`clean()`) и на уровне базы данных (`CheckConstraint`) - сработает даже при прямой вставке в БД в обход Django
- **Пересечение дат** - нельзя забронировать даты, которые уже заняты другим бронированием

---

## Мягкое удаление

Объявления (`Listing`) удаляются мягко - при вызове `.delete()` запись не пропадает из базы, а помечается полями `is_deleted=True` и `deleted_at=<время удаления>`.

- `Listing.objects` - показывает только неудалённые объявления (используется везде по умолчанию)
- `Listing.all_objects` - показывает все объявления, включая удалённые (для админки и отладки)

При удалении пользователя (`User`) его объявления не удаляются каскадно - поле `owner` просто становится `NULL` (`on_delete=SET_NULL`), сами объявления остаются в базе.

---

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `SECRET_KEY` | Секретный ключ Django |
| `DEBUG` | Режим отладки (True/False) |
| `ALLOWED_HOSTS` | Разрешённые хосты |
| `DB_NAME` | Имя базы данных |
| `DB_USER` | Пользователь БД |
| `DB_PASSWORD` | Пароль БД |
| `DB_HOST` | Хост БД |
| `DB_PORT` | Порт БД |
