from django.contrib.auth import login, logout
from rest_framework import serializers
from apps.users.repositories import UserRepository


class UserService:
    @staticmethod
    def register(validated_data):
        email = validated_data['email']
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
        login(request, user)

    @staticmethod
    def logout_user(request):
        logout(request)
