from django.contrib.auth.hashers import check_password,make_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from user_app.models import UserModel





class ChangePasswordView(APIView):

    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                old_password = request.data['old_password']
                new_password = request.data['new_password']
                confirm_password = request.data['confirm_password']
                user= UserModel.objects.get(email=request.user)
                check_old_pass = user.check_password(old_password)

                if not old_password:
                    return Response({'old_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
                if not new_password:
                    return Response({'new_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
                if not confirm_password:
                    return Response({'confirm_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

                if check_old_pass:

                    if check_password(new_password, user.password):
                        return Response({'status': False, 'message': 'Password alredy you have !'}, status=status.HTTP_400_BAD_REQUEST)

                    if new_password == confirm_password:
                        user.password = make_password(new_password)
                        user.save()
                        return Response({'status': True, 'message': 'Password changed successfully!'}, status=status.HTTP_200_OK)
                    else:
                        return Response({'status': False, 'message': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

                else:
                    return Response({'status': False, 'message': 'Old Password is wrong'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                if str(e.args[0]) == 'old_password':
                    return Response({'old_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
                elif str(e.args[0]) == 'new_password':
                    return Response({'new_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'confirm_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
