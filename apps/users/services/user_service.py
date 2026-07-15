from django.contrib.auth import login, logout
from rest_framework import serializers
from apps.users.repositories import UserRepository


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
        #
        # ВАЖНО: этот метод вызывается не только из LoginView, но и сразу после
        # успешной регистрации (см. RegisterView) - чтобы пользователь не должен был
        # вручную логиниться повторно сразу после того как создал аккаунт.
        login(request, user)

    @staticmethod
    def logout_user(request):
        # logout() удаляет данные сессии - следующий запрос от этого браузера снова
        # будет считаться анонимным, пока пользователь не залогинится заново
        logout(request)
