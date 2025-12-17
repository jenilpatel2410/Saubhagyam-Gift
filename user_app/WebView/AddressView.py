from rest_framework.response import Response
from rest_framework import status
from user_app.serializers import *  
from rest_framework.views import APIView



class CountriesAPI(APIView):
    def get(self,request,id=None):
        search = request.GET.get("search")
        if id:
            countries = CountryModel.objects.filter(pk=id)
            serializer = CountriesSerializer(countries, many = True)
            return Response({'status': True, 'data':serializer.data,'message':'Countries successfully fetched'},status=status.HTTP_200_OK)
        countries = CountryModel.objects.all()
        if search:
            countries = countries.filter(country_name__icontains=search)
        serializer = CountriesSerializer(countries, many=True)
        return Response({'status': True, 'data':serializer.data,'message':'Country successfully fetched'},status=status.HTTP_200_OK)
    

class StatesAPI(APIView):
    def get(self,request,id=None):
        country = request.GET.get("country")
        search = request.GET.get("search")
        
        if id:
            states = StatesModel.objects.filter(country=id)
            serializer = StateSerializer(states, many = True)
            return Response({'status': True, 'data':serializer.data,'message':'States successfully fetched'},status=status.HTTP_200_OK)
        states = StatesModel.objects.all()
        
        if country:
            states = states.filter(country_id=country)

        if search:
            states = states.filter(name__icontains=search)
            
        serializer = StateSerializer(states, many = True)
        return Response({'status': True, 'data':serializer.data,'message':'States successfully fetched'},status=status.HTTP_200_OK)
    
class CitiesAPI(APIView):
    def get(self,request,id=None):
        state = request.GET.get("state")
        search = request.GET.get("search")
        if id:
            cities = CitiesModel.objects.filter(state=id)
            serializer = CitiesSerializer(cities, many = True)
            return Response({'status': True, 'data':serializer.data,'message':'Cities successfully fetched'},status=status.HTTP_200_OK)
        cities = CitiesModel.objects.all()
        if state:
                cities = cities.filter(state_id=state)

        if search:
            cities = cities.filter(name__icontains=search)
                
        serializer = CitiesSerializer(cities, many = True)
        return Response({'status': True, 'data':serializer.data,'message':'Cities successfully fetched'},status=status.HTTP_200_OK)


class AddressAPI(APIView):

    def get(self,request,id=None):
        if request.user.is_authenticated:
            profile_user = UserModel.objects.get(email=request.user)
            if id is not None:
                try:
                    address = profile_user.address.get(id=id)
                    serializer = WebAddressSerializer(address,context={'request':request})
                    return Response({'status': True, 'data': serializer.data, 'message': 'Address successfully displayed'}, status=status.HTTP_200_OK)
                except AddressModel.DoesNotExist:
                    return Response({'status': False, 'message': 'Address not found'}, status=status.HTTP_200_OK)
            addresses = profile_user.address.all().order_by('-id')
            serializer = WebAddressSerializer(
                    addresses, many=True, context={'request': request})
            return Response({'status': True, 'data': serializer.data, 'message': 'Address successfully displayed'}, status=status.HTTP_200_OK)
          
        else:
            return Response({'status': False, 'message': "Login is required"}, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request):
        if request.user.is_authenticated:
            serializer = WebAddressSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                get_address = serializer.save()

                # Attach to UserModel
                up_obj = UserModel.objects.get(email=request.user)
                if not up_obj.address:
                    up_obj.address = get_address
                up_obj.address.add(get_address)
                up_obj.save()

                # Attach to ProfileModel
                user_profile = ProfileModel.objects.get(user=request.user)
                user_profile.addresses.add(get_address)
                user_profile.save()

                return Response({
                    'status': True,
                    'data': WebAddressSerializer(get_address, context={'request': request}).data,
                    'message': 'Address successfully added'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'status': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': "Login is required"}, status=status.HTTP_401_UNAUTHORIZED)
        
    def patch(self, request, id=None, format=None):
        if request.user.is_authenticated:
            if id is not None:
                try:
                    get_address = AddressModel.objects.get(id=id)
                    serializer = WebAddressSerializer(get_address,data=request.data,partial=True,context={'request':request})
                    if serializer.is_valid():
                        serializer.save()
                        return Response({'status': True, 'data': serializer.data, 'message': 'Address Data Updated'}, status=status.HTTP_200_OK)
                    else:
                        return Response({'status': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                except AddressModel.DoesNotExist:
                    return Response({'status': False, 'message': 'Address not found!'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'status': False, 'message': "Please select address for update"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': "Login is required"}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, id=None, format=None):
        if request.user.is_authenticated:
            if id is not None:
                try:
                    get_address = AddressModel.objects.get(id=id)
                    get_address.delete()
                    return Response({'status': True, 'message': 'Address successfully deleted'}, status=status.HTTP_200_OK)
                except AddressModel.DoesNotExist:
                    return Response({'status': False, 'message': 'Address does not exist!'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'status': False, 'message': "Please select address for deleting"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': "Login is required"}, status=status.HTTP_401_UNAUTHORIZED)