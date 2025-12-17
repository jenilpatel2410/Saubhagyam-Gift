from django.db.models import Q
from django.http import Http404, HttpResponse
from django.utils.text import slugify
from ..models import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import filters,generics
from management_app.serializer.ProductSerializer import MobileProductSerializer
from management_app.serializer.BrandSerializer import *
from management_app.serializer.OfferSerializer import *
from django.db.models import Count

class HomeList(APIView):
    def post(self,request):
        
        user_id = request.data.get('user_id')
        
        product=ProductModel.objects.order_by('-id')[:5]
        brand=BrandModel.objects.order_by('-id')[:5]
        offer=OfferSliderModel.objects.order_by('-id')[:5]
        populer_product=product
        newarrival=product
        limit = ProductModel.objects.filter(limited_stock="Yes").order_by('-id')[:5]
        bestsell=product    
        
        categories = (
            CategoryModel.objects.annotate(product_count=Count('product_single_category'))
            .filter(product_count__gt=0) 
            .order_by('-product_count')
        )
        
        category_products_data = {}
        
        for i, category in enumerate(categories[:3], start=1):
            products = ProductModel.objects.filter(category=category).order_by('-id')[:5]
            serialized_products = MobileProductSerializer(products, many=True, context={"request": request})
            category_products_data[f'category_{i}']  =  serialized_products.data
        
        productserialized=MobileProductSerializer(product,many=True, context={"request": request})
        brandserialized=MobileBrandSerializer(brand,many=True, context={"request": request})
        offerserializerd=MobileOfferSliderSerializer(offer,many=True, context={"request": request})
        populer_productserialized=MobileProductSerializer(populer_product,many=True, context={"request": request})
        newarrivalserializer = MobileProductSerializer(newarrival, many=True, context={"request": request})
        limitserializer=MobileProductSerializer(limit,many=True, context={"request": request})
        bestselling=MobileProductSerializer(bestsell,many=True, context={"request": request})

        data = {
            "status": True,
            "message": "List Product Successfully",
            "data": {
                "product": productserialized.data,
                "brand": brandserialized.data,
                "offer":offerserializerd.data,
                "populer_product":populer_productserialized.data,
                "new_arrivals": newarrivalserializer.data,
                "limited_stock_offers":limitserializer.data,
                "best_selling" :bestselling.data,
                **category_products_data,  
        
                
            }
        }
        return Response(data,status=status.HTTP_200_OK)
            
       