from apps.users.models import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def get_by_email(email):
        return User.objects.filter(email=email).first()

    @staticmethod
    def create(email, username, password, phone='', role=User.Role.TENANT):
        return User.objects.create_user(
            email=email,
            username=username,
            password=password,
            phone=phone,
            role=role,
        )

    @staticmethod
    def set_password(user, new_password):
        # set_password() хеширует пароль перед сохранением (не хранит открытым текстом)
        user.set_password(new_password)
        user.save()
        return user
