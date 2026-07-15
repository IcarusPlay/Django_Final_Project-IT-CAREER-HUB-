from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    # write_only=True - пароль можно ОТПРАВИТЬ в запросе, но он никогда не попадёт
    # обратно в ответ сервера (даже случайно) - важно для безопасности.
    # min_length=8 - простая защита от совсем слабых паролей уже на уровне валидации,
    # до того как Django попытается его захешировать
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'phone', 'role']

    def create(self, validated_data):
        # Специально НЕ используем стандартный User.objects.create() - у него пароль
        # сохранился бы обычным текстом. create_user() - специальный метод Django,
        # который автоматически хеширует пароль (превращает "testpass123" в длинную
        # нечитаемую строку через алгоритм PBKDF2) перед сохранением в базу.
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            role=validated_data.get('role', User.Role.TENANT),
        )
        return user


class LoginSerializer(serializers.Serializer):
    # Обычный Serializer (не ModelSerializer) - потому что это не создание/изменение
    # объекта модели, а просто проверка присланных данных (email+пароль)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # authenticate() - встроенная функция Django, которая ищет пользователя
        # с таким email и проверяет пароль (сравнивая хеши, а не текст напрямую).
        # username=data['email'] выглядит странно, но так и должно быть - раз в модели
        # User.USERNAME_FIELD = 'email', то authenticate() ожидает email именно
        # в параметре username (это просто название параметра функции, оно не связано
        # с реальным полем username модели)
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Неверный email или пароль')
        if not user.is_active:
            raise serializers.ValidationError('Аккаунт деактивирован')
        # Кладём найденного пользователя обратно в data - так LoginView сможет
        # забрать готовый объект через serializer.validated_data['user'],
        # не делая повторный запрос к базе
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    # Используется для ОТОБРАЖЕНИЯ данных пользователя (в ответах API) - в отличие
    # от RegisterSerializer, здесь намеренно нет поля password вообще
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']
