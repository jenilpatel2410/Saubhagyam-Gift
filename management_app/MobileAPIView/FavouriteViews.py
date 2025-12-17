from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.FavouriteSerializer import FavouriteSerializer
from management_app.serializer.ProductSerializer import MobileProductSerializer
from management_app.models import FavouriteModel, ProductModel
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated

class AddFavouriteAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):

        user_id = request.data.get('user_id')
        product_id = request.data.get('product_id')

        record = FavouriteModel.objects.filter(user_id=user_id, product_id=product_id).first()
        if record:
            record.save()
            return Response({'status':True, 'message':'Product Is Allready favourited'}, status=status.HTTP_200_OK)

        serializer = FavouriteSerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True, 'data':serializer.data, 'message':'Add To Favourite Successfully'}, status=status.HTTP_200_OK)
        return Response({'status':False, 'error':serializer.errors}, status=status.HTTP_200_OK)
    
class RemoveFavouriteAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user_id = request.data.get('user_id')
        product_id = request.data.get('product_id')
        
        if not user_id or not product_id:
            return Response({'status': False,
                             'message': 'user_id and product_id is required'},status=status.HTTP_200_OK)

        favourite = FavouriteModel.objects.filter(user_id=user_id, product_id=product_id)
        if favourite.exists():
            favourite.delete()
            return Response({'status':True, 'message':'Un Favourite Successfully'}, status= status.HTTP_200_OK) 
        else:
            return Response({'status':False, 'message':'Something Went to wrong'}, status=status.HTTP_400_BAD_REQUEST)

    
from management_app.translator import get_lang_code

class ListFavouriteAPI(APIView):
    def post(self, request):
        lang = get_lang_code(request)
        user_id = request.data.get('user_id')
        from_price = request.data.get('from_price')
        to_price = request.data.get('to_price')
        sort_by = request.data.get('filter')
        
        if not user_id:
            return Response({
                'status': False,
                'message': 'user_id is required'
            }, status= status.HTTP_200_OK)
    
        favourite_product = FavouriteModel.objects.filter(user_id=user_id).values_list('product_id', flat=True).exclude(deleted_at__isnull=False)

        products = ProductModel.objects.filter(id__in=favourite_product)

        if from_price and to_price: 
            products = products.filter(product_price__gte=from_price, product_price__lte=to_price)

        if sort_by == "high":
            products = products.order_by("-product_price")
        else:
            products = products.order_by("product_price")

        serializer = MobileProductSerializer(products, many=True, context={'request': request,'lang': lang})
        
        if not serializer.data:
            return Response({
                "status": False,
                "message": "Data Not Found",
                "errors": "Data Not Found"
            }, status=status.HTTP_200_OK)

        return Response({'status': True,'message': 'Favourites listed successfully',
                         'data': serializer.data}, status=status.HTTP_200_OK)
