import datetime
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from ..models import ProfileModel
from ..serializers import MobileUserSerializer
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code

class VerifyOtpAPIView(APIView):
    def post(self, request):
        mobile_no = request.data.get("contact")
        user_id = request.data.get("user_id")
        otp = request.data.get("otp")
        os_type = request.data.get("os_type")
        lang = get_lang_code(request) 

        if not otp:
            return Response(
                {"status": False, "message": t("OTP is required.", lang)},
                status=status.HTTP_200_OK,
            )

        if not mobile_no and not user_id:
            return Response(
                {"status": False, "message": t("Either user_id or mobile_no is required.", lang)},
                status=status.HTTP_200_OK,
            )

        try:
            if user_id:  
                profile = ProfileModel.objects.get(user__id=user_id)
            else:      
                profile = ProfileModel.objects.get(user__mobile_no=mobile_no)
        except ProfileModel.DoesNotExist:
            return Response(
                {"status": False, "message": t("User profile not found.", lang)},
                status=status.HTTP_200_OK,
            )

        # OTP match check
        if str(profile.otp) != str(otp):
            return Response(
                {
                    "status": False,
                    "message": t("Validation error.", lang),
                    "errors": t("Invalid OTP", lang),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # OTP verified → clear otp
        profile.otp = None
        if os_type:  
            profile.os_type = os_type
        profile.save()

        user = profile.user
        token, created = Token.objects.get_or_create(user=user)   # generate token
        user_data = MobileUserSerializer(user).data

        return Response(
            {
                "status": True,
                "message": t("OTP verified successfully.", lang),
                "token": token.key,
                "data": user_data,
            },
            status=status.HTTP_200_OK,
        )
