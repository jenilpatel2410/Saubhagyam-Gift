from django.db.models import Q
from django.http import Http404, HttpResponse
from django.utils.text import slugify
from ..models import *
import requests
import json 
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import filters,generics
from management_app.serializer.CategorySerializer import *
from django.conf import settings
from management_app.translator import get_lang_code

class CategoryList(APIView):
    def post(self,request):
        lang = get_lang_code(request)
        # queryset= CategoryModel.objects.all()
        queryset = CategoryModel.get_root_nodes().filter(is_active=True).order_by('id')
        serialized=MobileCategorySerializer(queryset,many=True,context={'lang': lang})
        
        data = {
            "status":True,
            "message":"List Category Successfully",
            "data": serialized.data
        }
        return Response(data, status=status.HTTP_200_OK)
    
class SubCategoryList(APIView):
    def post(self, request):
        category_id = request.data.get("category_id")
        lang = get_lang_code(request)
        if not category_id:
            return Response({
                "status": False,
                "message": "category_id is required"
            }, status=status.HTTP_200_OK)

        try:
            parent = CategoryModel.get_root_nodes().filter(is_active=True).order_by("id").get(id=category_id)
            
            subcategories = parent.get_children() 
            
            serializer = MobileSubCategorySerializer(subcategories, many=True,context={'lang': lang})

            return Response({
                "status": True,
                "message": "List Category Successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except CategoryModel.DoesNotExist:
            return Response({
                "status": False,
                "message": "Data not found",
                "errors": "Data Not Found"
            }, status=status.HTTP_200_OK)

        
