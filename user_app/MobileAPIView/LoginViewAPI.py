import random
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_app.Sms.Sms_service import MSG91Service2
from ..models import ProfileModel, FCMTokenModel
from ..serializers import MobileUserSerializer
from rest_framework.authtoken.models import Token
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code
from ..firebase_config import validate_token

def generate_otp():
    return random.randint(1000, 9999) 


class LoginView(APIView):
    def post(self, request):
        mobile = request.data.get("contact")
        firebase_token = request.data.get("firebase_token")
        lang = get_lang_code(request) 

        # if not validate_token(firebase_token):
        #     return Response({
        #         "status": False,
        #         "code": 400,
        #         "message": "The token is not registered with Firebase. Please ensure you are using the correct Firebase project configuration in your app.",
        #         "data": []
        #     }, status=status.HTTP_400_BAD_REQUEST)

        if not mobile:
            return Response(
                {"mobile": "This field is required."},
                status=status.HTTP_200_OK,
            )
        
        # if not mobile.startswith("+91"):
        #         mobile = f"+91{mobile}"

        try:
            profile = ProfileModel.objects.get(mobile_no=mobile)
        except ProfileModel.DoesNotExist:
            return Response(
                {"status": False, "message": t("Mobile number not registered!", lang)},
                status=status.HTTP_200_OK,
            )
            
        user = profile.user

        if not user.is_active:
            return Response(
                {"status": False, "message": t("User is deactivated. OTP not sent.", lang)},
                status=status.HTTP_200_OK,
            )

        # generate OTP
        otp_code = generate_otp()
        profile.otp = otp_code
        profile.otp_requested_at = timezone.now()
        profile.save()

        user = profile.user
        if firebase_token:
            user.token = firebase_token
            user.save(update_fields=["token"])
            
            FCMTokenModel.objects.update_or_create(
                user_id=user.id,
                defaults={"token": firebase_token}
            )

        profile.refresh_from_db()
        user_serializer = MobileUserSerializer(user)
        token,_ = Token.objects.get_or_create(user=user)
        # TODO: send OTP via SMS/Email gateway here
        # send_sms(mobile, f"Your OTP is {otp_code}")
        
        try:
            msg_service = MSG91Service2(authkey='351148ALYt1r4ponc5ff55ba1P1')
            
            online_template_id = '6708c95cd6fc054d1f010bd2'

            customer_mobile = str(profile.mobile_no)
            print(f"Customer Mobile (Login OTP): {customer_mobile}")
            
            # Send the SMS
            response = msg_service.send_message(
                template_id=online_template_id,
                mobiles=customer_mobile,
                var1=otp_code,
                var2="Saubhagyam"
            )                
            print(f"SMS Response (Login OTP): {response}")

        except Exception as e:
            print(f"An error occurred while sending SMS: {e}")
            pass

        return Response(
            {
                "status": True,
                "message": t("otp sent successfully", lang),
                "data" : user_serializer.data,
                "token" : "Token "+token.key
            },
            status=status.HTTP_200_OK,
        )





# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.contrib.auth import authenticate, login
# from rest_framework.authtoken.models import Token

# from ..models import UserModel


# class LoginView(APIView):
#     def post(self, request, format=None):
#         try:
#             email = request.data.get("email")
#             password = request.data.get("password")

#             # fields validation
#             if not email:
#                 return Response({"email": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
#             if not password:
#                 return Response({"password": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

#             # Check user exists
#             try:
#                 user_obj = UserModel.objects.get(email=email)
#             except UserModel.DoesNotExist:
#                 return Response(
#                     {"status": False, "message": "Please register to continue!"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Check active status
#             if not user_obj.is_active:
#                 return Response(
#                     {"status": False, "message": "Your account has been deactivated!"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Authenticate user
#             auth_user = authenticate(request=request, email=email, password=password)
#             if auth_user is None:
#                 return Response(
#                     {"status": False, "message": "Invalid credentials!"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Create / Get token
#             token_obj, _ = Token.objects.get_or_create(user=auth_user)

#             # (Optional: log user into session as well)
#             login(request, auth_user)

#             # Response data
#             data = {
#                 "id": auth_user.id,
#                 "first_name": auth_user.first_name,
#                 "last_name": auth_user.last_name,
#                 "email": auth_user.email,
#                 "role": auth_user.role.name if auth_user.role else None,
#                 "is_staff": auth_user.is_staff,
#                 "is_superuser": auth_user.is_superuser,
#                 "groups": [g.name for g in auth_user.groups.all()],
#                 "token": token_obj.key,
#             }

#             return Response(
#                 {"status": True, "data": data, "message": "User successfully logged in"},
#                 status=status.HTTP_200_OK,
#             )

#         except Exception as e:
#             return Response(
#                 {"status": False, "message": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )
