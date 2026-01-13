from django.contrib.auth.backends import ModelBackend
from user_app.models import UserModel

class EmailAdminBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        admin_user = getattr(request, 'user', None)

        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None
