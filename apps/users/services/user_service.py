from django.contrib.auth import login, logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers
from apps.users.repositories import UserRepository


# Стандартный Django-механизм для одноразовых токенов сброса пароля - тот же самый
# класс использует встроенная admin-панель Django. Токен зависит от текущего состояния
# пользователя (в том числе от хеша пароля) - если пароль уже сменили, старый токен
# автоматически станет недействительным, повторно использовать его нельзя.
token_generator = PasswordResetTokenGenerator()


class UserService:

    @staticmethod
    def register(validated_data):
        email = validated_data['email']
        # Дополнительная проверка на дубликат email - хотя поле email в модели уже
        # unique=True (база данных сама не даст создать два одинаковых), делаем проверку
        # заранее в Python, чтобы вернуть аккуратную ошибку с понятным текстом, а не
        # низкоуровневую ошибку целостности базы данных (IntegrityError)
        if UserRepository.get_by_email(email):
            raise serializers.ValidationError({'email': 'Пользователь с таким email уже существует'})
        return UserRepository.create(
            email=email,
            username=validated_data['username'],
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            role=validated_data.get('role', 'tenant'),
        )

    @staticmethod
    def login_user(request, user):
        # login() - встроенная функция Django. Она делает "магию" под капотом:
        # создаёт сессию, кладёт в неё id пользователя, и настраивает Response так,
        # чтобы браузеру ушла cookie с session_id. После этого при каждом следующем
        # запросе от этого браузера Django будет автоматически узнавать пользователя
        # по этой cookie - без неё пришлось бы передавать логин/пароль в каждом запросе.
        login(request, user)

    @staticmethod
    def logout_user(request):
        logout(request)

    @staticmethod
    def change_password(user, new_password):
        # Смена пароля залогиненным пользователем (знает старый пароль) -
        # проверка старого пароля происходит в сериализаторе, здесь только сохранение
        return UserRepository.set_password(user, new_password)

    @staticmethod
    def request_password_reset(email):
        # Генерируем токен для сброса пароля - НЕ показываем пользователю существует
        # ли такой email в базе или нет (это защита от "перебора email" - иначе можно
        # было бы узнать зарегистрирован ли конкретный человек на сайте). Поэтому метод
        # ничего не бросает если пользователь не найден - просто возвращает None,
        # а вьюха в любом случае отвечает одинаковым "успешным" сообщением.
        user = UserRepository.get_by_email(email)
        if not user:
            return None

        # uid - id пользователя, закодированный в urlsafe base64 (чтобы можно было
        # безопасно вставить в URL/JSON). token - одноразовый токен, привязанный
        # к текущему состоянию пользователя.
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # ПРИМЕЧАНИЕ ДЛЯ ЗАЩИТЫ ПРОЕКТА: в реальном продакшене здесь была бы отправка
        # email со ссылкой вида https://site.com/reset-password/?uid=...&token=...
        # (через django.core.mail.send_mail или сторонний сервис вроде SendGrid).
        # В рамках учебного проекта SMTP-сервер не настроен, поэтому uid и token
        # возвращаются прямо в ответе API - в реальном приложении это было бы
        # грубейшей дырой в безопасности (кто угодно мог бы сбросить чужой пароль,
        # просто зная email), но для демонстрации механизма на защите этого достаточно.
        return {'uid': uid, 'token': token}

    @staticmethod
    def confirm_password_reset(uid, token, new_password):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = UserRepository.get_by_id(user_id)
        except (TypeError, ValueError, OverflowError):
            user = None

        if not user or not token_generator.check_token(user, token):
            # Токен неверный, просроченный, либо уже был использован
            # (после смены пароля старый токен становится недействителен,
            # так как зависит от хеша пароля - это встроенное поведение Django)
            raise serializers.ValidationError('Ссылка для сброса пароля недействительна или устарела')

        return UserRepository.set_password(user, new_password)
