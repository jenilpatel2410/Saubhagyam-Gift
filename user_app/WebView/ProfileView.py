from rest_framework.response import Response
from rest_framework import status
from user_app.serializers import *  
from rest_framework.views import APIView


class WebProfileView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                get_profile = ProfileModel.objects.get(user=request.user)
                serializer = WebProfileSerializer(get_profile,context = {'request':request})
                return Response({'status':True,'data':serializer.data,'message':'Profile successfully retreived'},status=status.HTTP_200_OK)
            except:
                return Response({'status': False, 'message': "Profile does not exist for this user"}, status=status.HTTP_401_UNAUTHORIZED)
            
        else:
            return Response({'status':False,'message':'Login is required'},status=status.HTTP_401_UNAUTHORIZED)
        
    def patch(self,request):
        if request.user.is_authenticated:
            try:
                get_profile = ProfileModel.objects.get(user=request.user)
                serializer = WebProfileSerializer(get_profile, data=request.data, partial=True, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status':True,'data':serializer.data,'message':'Profile successfully updated'},status=status.HTTP_200_OK)
                return Response({'status':False,'message':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
            except ProfileModel.DoesNotExist:
                return Response({'status':False,'message':'Profile does not exist for this user'},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'status':False,'message':'Login is required'},status=status.HTTP_401_UNAUTHORIZED)
