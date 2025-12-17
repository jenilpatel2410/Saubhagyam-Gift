from django.contrib.auth import authenticate, login
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from management_app.models import Cart
from user_app.models import UserModel, VisitorModel, ProfileModel
import random
from ..serializers import WebUserSerializer
from django.utils import timezone
from management_app.translator import translate_text as t
from management_app.translator import get_lang_code
from user_app.Sms.Sms_service import MSG91Service2

def generate_otp():
    return random.randint(1000, 9999) 

class WebSignInView(APIView):
    def post(self, request):
        mobile = request.data.get("mobile_no")
        visitor_id = request.headers['visitor']
        lang = get_lang_code(request) 

        if not mobile:
            return Response(
                {"mobile_no": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not mobile.startswith("+"):
                mobile = f"+91{mobile}"

        try:
            profile = ProfileModel.objects.get(mobile_no=mobile)
        except ProfileModel.DoesNotExist:
            return Response(
                {"status": False, "message": t("Mobile number not registered!", lang)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # generate OTP
        otp_code = generate_otp()
        profile.otp = otp_code
        profile.otp_requested_at = timezone.now()
        profile.save()

        user = profile.user
       
        user_serializer = WebUserSerializer(user)
        token,_ = Token.objects.get_or_create(user=user)
        # TODO: send OTP via SMS/Email gateway here
        # send_sms(mobile, f"Your OTP is {otp_code}")
        
        try:
            msg_service = MSG91Service2(authkey='351148ALYt1r4ponc5ff55ba1P1')
            
            online_template_id = '6708c95cd6fc054d1f010bd2'

            customer_mobile = str(profile.mobile_no)
            
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

        login(request, user)
        user_cart = Cart.objects.filter(user__id=request.user.id)
        visitor_cart_items = Cart.objects.filter(visitor__visitor_id=visitor_id)
        for i in visitor_cart_items:
            if i.product.id in [i.product.id for i in user_cart]:
                for j in user_cart:
                    if i.product.id == j.product.id:
                        j.qty += i.qty
                        j.save()
                        i.delete()
            else:
                i.user = request.user
                i.visitor = None
                i.save()

        return Response(
            {
                "status": True,
                "message": t("otp sent successfully", lang),
                "data" : user_serializer.data,
                "token" : "Token "+token.key
            },
            status=status.HTTP_200_OK,
        )
        
    # def post(self, request, format=None):
    #     try:
    #         email = request.data['email']
    #         password = request.data['password']
    #         visitor_id = request.headers['visitor']
            

    #         if not email:
    #             return Response({'email': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
    #         if not password:
    #             return Response({'password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

    #         try:
    #             user_obj = UserModel.objects.get(email=email)
    #         except UserModel.DoesNotExist:
    #             return Response({'status': False, 'message': 'Please register to continue!'}, status=status.HTTP_400_BAD_REQUEST)

    #         if not user_obj.is_active:
    #             return Response({'status': False, 'message': 'Your account has been deactivated!'}, status=status.HTTP_400_BAD_REQUEST)

    #         auth_user = authenticate(username=email, password=password)
    #         if auth_user is not None:
    #             data = dict()
    #             obj, _ = Token.objects.get_or_create(user=auth_user)
    #             login(request, auth_user)

    #             mobile = ProfileModel.objects.get(user__email=email).mobile_no
    #             user_cart = Cart.objects.filter(user__id=request.user.id)
    #             visitor_cart_items = Cart.objects.filter(visitor__visitor_id=visitor_id)
    #             for i in visitor_cart_items:
    #                 if i.product.id in [i.product.id for i in user_cart]:
    #                     for j in user_cart:
    #                         if i.product.id == j.product.id:
    #                             j.qty += i.qty
    #                             j.save()
    #                             i.delete()
    #                 else:
    #                     i.user = request.user
    #                     i.visitor = None
    #                     i.save()
                
    #             data['id'] = auth_user.id
    #             data['first_name'] = auth_user.first_name
    #             data['last_name'] = auth_user.last_name
    #             data['group'] = str(auth_user.groups.all()[0])
    #             data['is_staff'] = auth_user.is_staff
    #             data['is_superuser'] = auth_user.is_superuser
    #             data['email'] = auth_user.email
    #             data['phone_no'] = str(mobile)
    #             data['token'] = obj.key

    #             cart_items = Cart.objects.filter(user__id=request.user.id)
    #             data['cart_counter'] = cart_items.count()

    #             return Response({'status': True, 'data': data, 'message': 'User successfully logged in'}, status=status.HTTP_200_OK)
    #         else:
    #             return Response({'status': False, 'message': 'Invalid credentials!'}, status=status.HTTP_400_BAD_REQUEST)
    #     except UserModel.DoesNotExist:
    #         return Response({'status': False, 'message': 'Invalid credentials!'}, status=status.HTTP_400_BAD_REQUEST)
    #     except Exception as e:
    #         if str(e.args[0]) == 'email':
    #             return Response({'email': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
    #         elif str(e.args[0]) == 'password':
    #             return Response({'password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
    #         else:
    #             return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        