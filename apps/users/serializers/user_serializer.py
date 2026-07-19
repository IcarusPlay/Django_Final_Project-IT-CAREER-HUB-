from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    # write_only=True - пароль можно ОТПРАВИТЬ в запросе, но он никогда не попадёт
    # обратно в ответ сервера (даже случайно) - важно для безопасности.
    #
    # ВАЖНО (исправление замечания преподавателя): раньше здесь стояла только
    # min_length=8 - примитивная проверка длины. Но в settings.py уже настроены
    # AUTH_PASSWORD_VALIDATORS - стандартный набор правил Django (пароль не должен
    # быть похож на email/username, не должен быть слишком распространённым вроде
    # "password123", не должен состоять только из цифр). Раньше эти правила
    # проверялись ТОЛЬКО при создании пользователя через Django Admin/CLI, но не
    # при регистрации через наш API - потому что DRF-сериализаторы не вызывают
    # валидаторы паролей автоматически, в отличие от стандартных Django-форм.
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'phone', 'role']

    def validate_password(self, value):
        # validate_password() - функция Django, которая прогоняет пароль через
        # ВСЕ валидаторы, перечисленные в settings.AUTH_PASSWORD_VALIDATORS.
        # Передаём user=None, потому что на этом этапе объект пользователя ещё
        # не создан - но некоторые валидаторы (например UserAttributeSimilarityValidator,
        # который проверяет "не похож ли пароль на email") умеют работать и без него,
        # используя self.initial_data для сравнения с email/username из текущего запроса.
        try:
            # Собираем "черновик" пользователя из данных запроса - не сохраняем его
            # в базу, просто передаём валидатору, чтобы он мог сравнить пароль
            # с email/username именно ЭТОГО регистрирующегося человека
            dummy_user = User(
                email=self.initial_data.get('email', ''),
                username=self.initial_data.get('username', ''),
            )
            validate_password(value, user=dummy_user)
        except DjangoValidationError as e:
            # Django-валидатор кидает свою ValidationError (со списком сообщений),
            # а DRF ожидает свою - конвертируем одно в другое, иначе ошибка
            # потерялась бы или улетела как 500 Internal Server Error
            raise serializers.ValidationError(list(e.messages))
        return value

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


class ChangePasswordSerializer(serializers.Serializer):
    # Смена пароля для уже залогиненного пользователя - требует знания
    # СТАРОГО пароля (защита от того, чтобы кто-то, получивший доступ
    # к чужой открытой сессии в браузере, мог тихо сменить пароль)
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        # check_password() сравнивает переданный пароль с хешем в базе -
        # безопасное сравнение, не через == с открытым текстом
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль')
        return value

    def validate_new_password(self, value):
        # Тот же самый набор правил из AUTH_PASSWORD_VALIDATORS применяется
        # и здесь - новый пароль должен быть не хуже, чем при регистрации
        user = self.context['request'].user
        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def save(self):
        user = self.context['request'].user
        # set_password() хеширует новый пароль (не сохраняет как открытый текст)
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        # Те же самые правила из AUTH_PASSWORD_VALIDATORS, что и при регистрации -
        # новый пароль после сброса должен быть не слабее исходных требований
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
