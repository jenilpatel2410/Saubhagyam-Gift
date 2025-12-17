import random
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import MobileUserSerializer
from ..models import ProfileModel
from management_app.models import ContactModel

class SignUpView(APIView):
    def post(self, request, format=None):
        email = request.data.get('email')
        mobile_no = request.data.get('contact')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not email or not mobile_no or not first_name or not last_name:
            return Response(
                {'status': False, 'message': 'Email, Mobile no, First name, Last name and token are required'},
                status=status.HTTP_200_OK
            )
        
        # if mobile_no and not mobile_no.startswith("+91"):
        #     mobile_no = f"+91{mobile_no}"

        try:
            if ProfileModel.objects.filter(mobile_no=mobile_no).exists():
                return Response(
                    {'status': False, 'message': f'Mobile number {mobile_no} already exists'},
                    status=status.HTTP_200_OK
                )
            
            request_data = request.data.copy()
            request_data['mobile_no'] = mobile_no

            serializer = MobileUserSerializer(data=request_data)
            if serializer.is_valid():
                    user = serializer.save()

                    # Generate 6 digit OTP (not sent, only stored)
                    otp = random.randint(1000, 9999)

                    # Save ProfileModel with OTP
                    ProfileModel.objects.create(
                        user=user,
                        mobile_no=mobile_no,
                        otp=otp,
                        otp_requested_at=timezone.now()
                    )
                    ContactModel.objects.create(
                        user=user,
                        contact_type="Individual",
                        contact_role=ContactModel.ContactRoleChoices.customer,
                        name=f"{first_name} {last_name}".strip(),
                        phone_no=mobile_no,
                        email=email,
                        is_active=True
                    )
                    

                    user.refresh_from_db()   # ensures profile is loaded
                    response_serializer = MobileUserSerializer(user)

                    return Response(
                        {
                            'status': True,
                            'message': 'User created successfully.',
                            'data': response_serializer.data
                        },
                        status=status.HTTP_201_CREATED
                    )
            else:
                return Response(
                    {'status': False, "message": f'User already exists with given email - {email}', 'errors': serializer.errors},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response({'error': "Something went wrong", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

