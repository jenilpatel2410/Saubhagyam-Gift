from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from user_app.models import ProfileModel,UserModel
from ..serializers import WebUserSerializer
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from management_app.models import ContactModel
import random
from django.utils import timezone


class WebSignUpView(APIView):

    def post(self, request, format=None):
        email = request.data.get('email')
        mobile_no = request.data.get('mobile_no')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not email or not mobile_no or not first_name or not last_name:
            return Response({'status': False, 'message': 'Email, Mobile no, First name and Last name'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if ProfileModel.objects.filter(mobile_no=mobile_no).exists():
                return Response({'status': False, 'message': 'Mobile number already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
            if UserModel.objects.filter(email=email).exists():
                return Response({'status': False, 'message': f'Email "{email}" already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
            user_data = {}
            serializer = WebUserSerializer(data=request.data)
            if serializer.is_valid():
                # if request.data['password'] == request.data['confirm_password']:
                    user = serializer.save()
                        # password=make_password(request.data['password']))
                    # user_token = Token.objects.create(user=user)

                    user_profile = ProfileModel.objects.create(
                        user=user, mobile_no=request.data.get('mobile_no'))
                    user_contact = ContactModel.objects.create(
                                    user=user,
                                    contact_type="Individual",
                                    contact_role=ContactModel.ContactRoleChoices.customer,
                                    name=f"{first_name} {last_name}".strip(),
                                    phone_no=mobile_no,
                                    email=email,
                                    is_active=True
                                )
                    customerGroup, _ = Group.objects.get_or_create(
                        name='Customer')
                    customerGroup.user_set.add(user)
                    user_data = serializer.data
                    try:
                        from_email = settings.EMAIL_HOST_USER
                        to_email = [user.email]
                        subject = "Welcome to Saubhagyam!"
                        html_content = render_to_string('welcome_register_mail.html',{'user_name':f'{user.first_name} {user.last_name}','shopping':'https://olivedrab-caribou-708347.hostingersite.com/'})
            
                        # Send email
                        email = EmailMultiAlternatives(subject, html_content, from_email, to_email)
                        email.attach_alternative(html_content, "text/html")
                        email.send()
                                
                    except Exception as e:
                        print("EMAIL ERROR:", e)
                        pass

                    return Response({'status': True, 'data': user_data, 'message': 'User successfully registered'}, status=status.HTTP_201_CREATED)
                    
                # else:
                #     return Response({'status': False, 'message': 'Password does not match'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                for i in serializer.errors:
                    print(i, serializer.errors[i])
                    return Response({'status': False, "message": f'User already exists with given email - {email} - {serializer.errors}'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # if str(e.args[0]) == 'password':
            #     return Response({'password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
            # elif str(e.args[0]) == 'confirm_password':
            #     return Response({'confirm_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
            # else:
                return Response({'error': "Something went wrong", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
