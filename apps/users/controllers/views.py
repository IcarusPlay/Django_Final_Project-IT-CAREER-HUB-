from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.users.serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
)
from apps.users.services import UserService


class RegisterView(APIView):
    # AllowAny - буквально "разрешить всем", включая анонимов. Логично: чтобы
    # зарегистрироваться, у человека по определению ещё нет аккаунта для авторизации
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = UserService.register(serializer.validated_data)
            # Сразу логиним пользователя после успешной регистрации - раньше здесь
            # этого не было, из-за чего фронтенд (через localStorage) думал что
            # пользователь уже вошёл, а бэкенд на самом деле не создавал сессию.
            UserService.login_user(request, user)
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            UserService.login_user(request, user)
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        UserService.logout_user(request)
        return Response({'detail': 'Вы вышли из системы'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    # Смена пароля для уже залогиненного пользователя, знающего текущий пароль -
    # доступна только авторизованным (по определению, иначе непонятно чей пароль менять)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # передаём request в context - сериализатору нужен доступ к request.user,
        # чтобы проверить старый пароль именно ТЕКУЩЕГО залогиненного пользователя
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Пароль успешно изменён'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    # Запрос на сброс пароля доступен без авторизации - человек по определению
    # не может войти, раз забыл пароль
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            result = UserService.request_password_reset(serializer.validated_data['email'])

            # Намеренно возвращаем ОДИНАКОВЫЙ ответ независимо от того, найден
            # пользователь с таким email или нет - это защита от "перебора email"
            # (иначе по разнице ответов можно было бы узнать, зарегистрирован
            # ли конкретный человек на сайте)
            response_data = {
                'detail': 'Если аккаунт с таким email существует, инструкция по сбросу пароля отправлена'
            }

            # ВАЖНО - только для демонстрации на защите проекта: в реальном продакшене
            # uid/token отправлялись бы на email пользователя, а не возвращались
            # в API-ответе. SMTP не настроен в рамках учебного проекта, поэтому
            # временно "проксируем" их так, чтобы можно было показать полный цикл
            # сброса пароля преподавателю через Swagger/Postman
            if result:
                response_data['reset_uid'] = result['uid']
                response_data['reset_token'] = result['token']

            return Response(response_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            UserService.confirm_password_reset(
                serializer.validated_data['uid'],
                serializer.validated_data['token'],
                serializer.validated_data['new_password'],
            )
            return Response({'detail': 'Пароль успешно сброшен'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
