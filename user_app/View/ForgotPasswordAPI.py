from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from user_app.models import PasswordResetLinkModel, UserModel
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta

class ForgotPasswordSendLinkView(APIView):
    def post(self, request, format=None):
        try:
            email = request.data['email']
            http_referer = request.META.get('HTTP_REFERER',None)
            get_user = UserModel.objects.get(email=email)
            new_reset_obj = PasswordResetLinkModel.objects.create(user=get_user)
            new_reset_obj.url_link = f"{http_referer}reset-password/{new_reset_obj.reset_uuid}" #{base_url}
            new_reset_obj.save()
            
            # Render email content
            reset_link = new_reset_obj.url_link
            subject = "Password Reset Request"
            from_email = settings.EMAIL_HOST_USER
            to_email = [get_user.email]
            html_content = render_to_string('password_reset_email.html', {'reset_link': reset_link})
            
            # Send email
            email = EmailMultiAlternatives(subject, html_content, from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            return Response({'status': True, 'message': "A password reset link has been sent to your registered email!"}, status=status.HTTP_200_OK)
        except UserModel.DoesNotExist:
            return Response({'message': "Given email is not registered!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ForgotPasswordFormView(APIView):
    def post(self, request, reset_token=None, format=None):
        try:
            fetch_user = PasswordResetLinkModel.objects.filter(reset_uuid = reset_token , created_at__gte =timezone.now() - timedelta(minutes=10) ).first()
            if not fetch_user:
                return Response({
                    'status': False,
                    'message': "Password reset link expired or invalid. Generate a new one!"
                }, status=status.HTTP_400_BAD_REQUEST)
        except (PasswordResetLinkModel.DoesNotExist,ValidationError):
            return Response({'status': False,'message': f"Password rest link expired or invalid generate new one!"}, status=status.HTTP_400_BAD_REQUEST)
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        if new_password == '' or new_password is None:
            return Response({'status': False,'message': "Enter new password!"}, status=status.HTTP_400_BAD_REQUEST)
        if confirm_password == '' or confirm_password is None:
            return Response({'status': False,'message': "Enter confirm password!"}, status=status.HTTP_400_BAD_REQUEST)
        if new_password == confirm_password:
            
            get_user = UserModel.objects.get(email=fetch_user.user.email)
            get_user.password = make_password(new_password)
            get_user.save()
            return Response({'status': True, 'message': 'Password successfully reset. you can login now'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': False, 'message': 'Password does not match'}, status=status.HTTP_400_BAD_REQUEST)
       