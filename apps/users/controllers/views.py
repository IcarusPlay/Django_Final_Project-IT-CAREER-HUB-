from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.users.serializers import RegisterSerializer, LoginSerializer, UserSerializer
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
            # Первое же действие требующее авторизации (например создание объявления)
            # падало с "Authentication credentials were not provided". Теперь
            # регистрация = регистрация + автоматический вход одним действием.
            UserService.login_user(request, user)
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # LoginSerializer.validate() уже проверил email+пароль через Django's
            # authenticate() и положил найденного пользователя в validated_data['user']
            # (см. serializers/user_serializer.py) - здесь просто забираем готовый объект
            user = serializer.validated_data['user']
            UserService.login_user(request, user)
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    # Выйти может только тот, кто уже вошёл - IsAuthenticated логично здесь
    permission_classes = [IsAuthenticated]

    def post(self, request):
        UserService.logout_user(request)
        return Response({'detail': 'Вы вышли из системы'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Простой способ фронтенду узнать "кто я сейчас" - используется например
        # при первой загрузке страницы, чтобы проверить жива ли ещё сессия
        return Response(UserSerializer(request.user).data)
