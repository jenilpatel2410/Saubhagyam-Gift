from rest_framework.response import Response
from rest_framework import status
from user_app.serializers import *  
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

# class CountriesAPI(APIView):
#     def get(self,request,id=None):
#         if id:
#             countries = CountryModel.objects.filter(pk=id)
#             serializer = CountriesSerializer(countries, many = True)
#             return Response({'status': True, 'data':serializer.data,'message':'Countries successfully fetched'},status=status.HTTP_200_OK)
#         countries = CountryModel.objects.all()
#         serializer = CountriesSerializer(countries, many=True)
#         return Response({'status': True, 'data':serializer.data,'message':'Country successfully fetched'},status=status.HTTP_200_OK)
    

# class StatesAPI(APIView):
#     def get(self,request,id=None):
#         if id:
#             states = StatesModel.objects.filter(country=id)
#             serializer = StateSerializer(states, many = True)
#             return Response({'status': True, 'data':serializer.data,'message':'States successfully fetched'},status=status.HTTP_200_OK)
#         states = StatesModel.objects.all()
#         serializer = StateSerializer(states, many = True)
#         return Response({'status': True, 'data':serializer.data,'message':'States successfully fetched'},status=status.HTTP_200_OK)
    
# class CitiesAPI(APIView):
#     def get(self,request,id=None):
#         if id:
#             cities = CitiesModel.objects.filter(state=id)
#             serializer = CitiesSerializer(cities, many = True)
#             return Response({'status': True, 'data':serializer.data,'message':'Cities successfully fetched'},status=status.HTTP_200_OK)
#         cities = CitiesModel.objects.all()
#         serializer = CitiesSerializer(cities, many = True)
#         return Response({'status': True, 'data':serializer.data,'message':'Cities successfully fetched'},status=status.HTTP_200_OK)


class AddressListView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"status": False, "message": "user_id is required"},
                status=status.HTTP_200_OK,
            )
        user = get_object_or_404(UserModel, id=user_id)
        addresses = user.address.all()  
        serializer = AddressSerializer(addresses, many=True)
        if not addresses.exists():  # if no addresses found
            return Response(
                {
                    "status": False,
                    "message": "Data Not Found",
                    "data": None,
                    "errors": "Data Not Found",
                },
                status=status.HTTP_200_OK,
            )
        
        data_with_user_id = []
        for item in serializer.data:
            item_with_user = dict(item)
            item_with_user["user_id"] = user.id
            data_with_user_id.append(item_with_user)
        return Response(
            {
                "status": True,
                "message": "Address successfully fetched",
                "data": data_with_user_id,
            },
            status=status.HTTP_200_OK,
        )

class AddressCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"status": False, "message": "user_id is required"},
                status=status.HTTP_200_OK,
            )

        user = get_object_or_404(UserModel, id=user_id)

        # Check if address already exists for this user
        existing_address = user.address.first()  # since you want only one address

        if existing_address:
            # Update existing address
            serializer = AddressSerializer(existing_address, data=request.data, partial=True)
        else:
            # Create new address
            serializer = AddressSerializer(data=request.data)

        if serializer.is_valid():
            address = serializer.save()
            # Link only if new
            if not existing_address:
                user.address.add(address)

            response_data = dict(serializer.data)
            response_data["user_id"] = user_id

            return Response(
                {
                    "status": True,
                    "message": "Address updated successfully" if existing_address else "Address added successfully",
                    "data": response_data,
                },
                status=status.HTTP_200_OK if existing_address else status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_200_OK)