from rest_framework.response import Response
from rest_framework import status
from management_app.serializers import *
from .models import *
from user_app.models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
import csv
import openpyxl
from openpyxl.styles import Font
from django.http import HttpResponse
from .pagination import ListPagination
from django.conf import settings

class CountryView(APIView):
    def get(self,request):
        countries = CountryModel.objects.all()
        paginator = ListPagination()
        paginated_countries = paginator.paginate_queryset(countries,request)
        serializer = CountrySerializer(paginated_countries,many=True)

        return paginator.get_paginated_response(serializer.data)
    


class SerialNoView(APIView):
    def get(self,request):
        serial_nos = SerialNumbersModel.objects.all()
        search = request.query_params.get('search','')
        if search:
            serial_nos = SerialNumbersModel.objects.filter(Q(serial_no__icontains=search) |
                                                           Q(product__name__icontains=search)

            )
        paginator = ListPagination()
        paginated_serial_nos = paginator.paginate_queryset(serial_nos,request)
        serializer = SerialNoSerializer(paginated_serial_nos,many=True)

        return paginator.get_paginated_response(serializer.data)
    

    def post(self,request):
        data = request.data
        serializer = SerialNoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Serial no. Successfully added'})
        
        return Response({'status':False,'errors':serializer.errors})
    
    def patch(self,request,id):
        try:
            serial_no = SerialNumbersModel.objects.get(id=id)
            serializer = SerialNoSerializer(serial_no,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Serial no. Successfully updated'})
            return Response({'status':False,'errors':serializer.errors})
        except SerialNumbersModel.DoesNotExist:
            return Response({'status':False,'message':'Serial no. not available'},status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self,request,id):
        try:
            serial_no = SerialNumbersModel.objects.get(id=id)
            serial_no.delete()
            return Response({'status':True,'message':'Serial no. Successfully deleted'})

        except SerialNumbersModel.DoesNotExist:
           return Response({'status':False,'message':'Serial no. not available'},status=status.HTTP_400_BAD_REQUEST)


        
class UnitView(APIView):
    def get(self, request):
        data = [
            {"value": "pcs", "label": "Piece"},
            {"value": "set", "label": "Set"},
            {"value": "pair", "label": "Pair"},
            {"value": "box", "label": "Box"},
            {"value": "pack", "label": "Pack"},
            {"value": "dozen", "label": "Dozen"},
            {"value": "bundle", "label": "Bundle"},
            {"value": "roll", "label": "Roll"},
            {"value": "sheet", "label": "Sheet"},
            {"value": "book", "label": "Book"},
            {"value": "card", "label": "Card"},
            {"value": "bottle", "label": "Bottle"},
            {"value": "jar", "label": "Jar"},
        ]

        gsts = [
            {"value": 5.0, "label": "5%"},
            {"value": 12.0, "label": "12%"},
            {"value": 18.0, "label": "18%"},
        ]

        return Response(
            {"status": True, "data": data, "gsts": gsts},
            status=status.HTTP_200_OK
        )
