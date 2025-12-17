from rest_framework.response import Response
from rest_framework import status
from user_app.serializers import *  
from rest_framework.views import APIView

class ContactUsView(APIView):
    def post(self,request):
         try:
             serializer = ContactUsSerializer(data=request.data)
             if serializer.is_valid():
                 serializer.save()
                 return Response({'status': True, 'message': 'Contact us form submitted successfully'}, status=status.HTTP_201_CREATED)
             return Response({'status': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
         except Exception as e:
             return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
