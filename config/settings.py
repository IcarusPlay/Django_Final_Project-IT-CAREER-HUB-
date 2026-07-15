from pathlib import Path
import environ

# BASE_DIR - абсолютный путь к корню проекта. Используется дальше как отправная точка
# для всех остальных путей (файл .env, папка media, static и т.д.)
BASE_DIR = Path(__file__).resolve().parent.parent

# django-environ - библиотека для удобной работы с переменными окружения из файла .env.
# read_env() читает файл .env и загружает его содержимое в os.environ - дальше можно
# доставать значения через env.str(), env.bool(), env.list()
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# Все секреты (пароли, ключи) читаются из .env, а не хардкодятся в коде - файл .env
# добавлен в .gitignore и никогда не попадает в git-репозиторий
SECRET_KEY = env.str('SECRET_KEY')
DEBUG = env.bool('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')  # список доменов/IP, с которых разрешено обращаться к серверу


INSTALLED_APPS = [
    # стандартные встроенные приложения Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # сторонние библиотеки
    'rest_framework',       # Django REST Framework - весь функционал API
    'django_filters',       # готовые классы фильтрации для DRF
    'drf_spectacular',      # автогенерация Swagger/OpenAPI документации

    # наши собственные приложения
    'apps.users',
    'apps.listings',
    'apps.bookings',
    'apps.reviews',
]

# Middleware - это "прослойки", через которые проходит КАЖДЫЙ запрос по очереди сверху вниз,
# и КАЖДЫЙ ответ - в обратном порядке снизу вверх. Порядок в списке важен.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',       # обрабатывает cookie сессии
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',                   # защита от CSRF-атак
    'django.contrib.auth.middleware.AuthenticationMiddleware',      # прикрепляет request.user
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'  # где искать главный список маршрутов проекта

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # DIRS - где искать HTML-шаблоны для фронтенда (index.html, listing.html и т.д.)
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Настройки подключения к базе данных - все значения тоже берутся из .env,
# чтобы на разных машинах (у тебя локально / у преподавателя / на сервере)
# можно было использовать разные пароли и хосты без изменения кода
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env.str('DB_NAME'),
        'USER': env.str('DB_USER'),
        'PASSWORD': env.str('DB_PASSWORD'),
        'HOST': env.str('DB_HOST'),
        'PORT': env.str('DB_PORT'),
    }
}

# Встроенные в Django правила проверки паролей при регистрации -
# не слишком похож на username/email, не слишком короткий, не из списка популярных паролей,
# не состоит только из цифр
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Говорим Django использовать НАШУ кастомную модель пользователя вместо стандартной -
# без этой строки все ссылки на "пользователя" в системе указывали бы на стандартный
# django.contrib.auth.models.User, а не на apps.users.models.User
AUTH_USER_MODEL = 'users.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Berlin'  # важно для корректной работы дат бронирования
USE_I18N = True
USE_TZ = True                # хранить даты/время в базе в UTC, конвертировать в TIME_ZONE при показе

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  # тип поля id по умолчанию для всех моделей


# Настройки Django REST Framework - применяются глобально ко ВСЕМ view проекта,
# если конкретная view явно не переопределяет какую-то настройку
REST_FRAMEWORK = {
    # Сессионная аутентификация - вход через cookie браузера (см. подробности
    # в apps/users/services/user_service.py, комментарий к login_user())
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    # По умолчанию GET-запросы разрешены всем, а изменяющие (POST/PUT/DELETE) -
    # только авторизованным. Конкретные view могут переопределить это своим
    # permission_classes (например AllowAny для регистрации)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # CursorPagination - более безопасный вид пагинации чем обычная "номер страницы":
    # он не позволяет угадать общее количество записей или перепрыгнуть на произвольную
    # страницу, вместо номера использует непрозрачный "курсор" (закодированную позицию)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.CursorPagination',
    'PAGE_SIZE': 6,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # для автогенерации Swagger
}


# Настройки drf-spectacular - что выводится на странице /api/docs/ (Swagger UI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Rental Housing API',
    'DESCRIPTION': 'API for a home rental platform - listings, bookings, reviews',
    'VERSION': '1.9',
    'SERVE_INCLUDE_SCHEMA': False,
}


# --- Логирование ---
# Настроено три отдельных "потока" логов, каждый пишется в своё место:
# 1) общие логи Django (запуск сервера, ошибки) - в консоль, чтобы сразу видеть при разработке
# 2) все HTTP-запросы - в отдельный файл, для анализа истории обращений к серверу
# 3) все SQL-запросы к базе данных - в отдельный файл, полезно для отладки производительности
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)  # создаём папку logs автоматически при первом запуске, если её нет

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console_fmt': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
        'file_fmt': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console_fmt',
        },
        'http_file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'http_logs.log',
            'formatter': 'file_fmt',
            'encoding': 'utf-8',
        },
        'db_file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'db_logs.log',
            'formatter': 'file_fmt',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        # 'django' - логгер верхнего уровня Django (запуск, системные сообщения) - в консоль
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # 'django.request' - логи КАЖДОГО обработанного HTTP-запроса - в отдельный файл
        'django.request': {
            'handlers': ['http_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # 'django.db.backends' - логи каждого SQL-запроса к базе данных - в отдельный файл.
        # Очень подробно (DEBUG), полезно чтобы увидеть реальные SQL-запросы,
        # которые генерирует Django ORM за кулисами
        'django.db.backends': {
            'handlers': ['db_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


# Статика - CSS/JS файлы фронтенда
STATICFILES_DIRS = [BASE_DIR / 'static']       # откуда Django берёт статику в разработке
STATIC_ROOT = BASE_DIR / 'staticfiles'          # куда собирать статику для продакшена (collectstatic)


# Медиа - загружаемый пользователями контент (картинки объявлений)
MEDIA_URL = '/media/'             # по какому URL картинки доступны в браузере
MEDIA_ROOT = BASE_DIR / 'media'   # в какую папку на диске реально сохраняются файлы
