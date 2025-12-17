from rest_framework.response import Response
from rest_framework import status
from user_app.serializers import *  
from rest_framework.views import APIView

class crmAddressAPI(APIView):
    def post(self, request):
        user_id = request.data.get('user')
        if user_id:
            serializer = WebAddressSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                get_address = serializer.save()

                # Attach to UserModel
                up_obj = UserModel.objects.get(id=user_id)
                if not up_obj.address:
                    up_obj.address = get_address
                up_obj.address.add(get_address)
                up_obj.save()
                
                user_profile = ProfileModel.objects.get(user=user_id)
                user_profile.addresses.add(get_address)
                user_profile.save()
                
                user_contact = ContactModel.objects.filter(user=user_id).first()
                if user_contact:
                    user_contact.many_address.add(get_address)
                    user_contact.save()

                return Response({
                    'status': True,
                    'data': WebAddressSerializer(get_address, context={'request': request}).data,
                    'message': 'Address successfully added'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'status': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': "user is required"}, status=status.HTTP_401_UNAUTHORIZED)
        
    def delete(self, request, id=None, format=None):
            if id is not None:
                try:
                    get_address = AddressModel.objects.get(id=id)
                    get_address.delete()
                    return Response({'status': True, 'message': 'Address successfully deleted'}, status=status.HTTP_200_OK)
                except AddressModel.DoesNotExist:
                    return Response({'status': False, 'message': 'Address does not exist!'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'status': False, 'message': "Please select address for deleting"}, status=status.HTTP_400_BAD_REQUEST)
            