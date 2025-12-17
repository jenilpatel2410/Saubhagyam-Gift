from rest_framework.response import Response
from rest_framework.views import APIView
from user_app.models import UserModel


class DeactivateAccountAPI(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            user = UserModel.objects.get(email=request.user)
            if user.is_active:
                user.is_active = False
                user.save()
                return Response({"status": True, "message": "Your account has been successfully deactivated!"})
            else:
                return Response({"status": False, "message": "Your account is already deactivated!"})
        else:
            return Response({"status": False, "message": "Please login first!"})
