from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.InventorySerializer import *
from ..models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
from decimal import Decimal, InvalidOperation
import csv
import openpyxl, io
from django.http import HttpResponse
from openpyxl.styles import Font
from ..pagination import ListPagination
from io import BytesIO
from datetime import datetime
from django.conf import settings
from django.utils.timezone import localtime



class InventoryView(APIView):

    def get(self, request, id=None):
        if id:
            inventories = Inventory.objects.filter(id=id)
            if not inventories.exists():
                return Response({
                    'status': False,
                    'message': 'Inventory not found',
                    'error': 'Inventory not found'
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = InventorySerializer(inventories, many=True)
            return Response({
                'status': True,
                'message': "Inventory Retrieved Successfully",
                'data': serializer.data
            }, status = status.HTTP_200_OK)

        else:
            inventories = Inventory.objects.all().order_by('-id')

            # Search filter
            search = request.query_params.get('search', '')
            if search:
                inventories = inventories.filter(
                    Q(product__name__icontains=search) |
                    Q(serialno__serial_no__icontains=search)
                )

            # Check if 'all=true'
            all_records = request.query_params.get('all', False)

            paginator = ListPagination()
            if all_records and all_records in ['1', 'true', 'True', True]:
                paginated_inventories = None
            else:
                paginated_inventories = paginator.paginate_queryset(inventories, request)

            # If paginated, return paginated response
            if paginated_inventories is not None:
                serializer = InventorySerializer(paginated_inventories, many=True)
                return paginator.get_paginated_response(serializer.data)

            # If 'all=true', return all data
            serializer = InventorySerializer(inventories, many=True)
            return Response({
                'status': True,
                'message': "List Inventory Successfully",
                'data': serializer.data
            }, status = status.HTTP_200_OK)     
    
    def post(self,request):
        serializer = InventorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Inventory Product Successfully added'})
        return Response({'status':False,'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request,id):
        try:
           inventory = Inventory.objects.get(id=id)
           serializer = InventorySerializer(inventory,data=request.data,partial=True)
           if serializer.is_valid():
               serializer.save()
               return Response({'status':True,'data':serializer.data,'message':'Inventory Updated Successfully'})
           return Response({'status':False,'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except Inventory.DoesNotExist:
            return Response({'status':False,'message':'Inventory not found'},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self,request,id):
        try:
            inventory = Inventory.objects.get(id=id)
            inventory.delete()
            return Response({'status':True,'message':'Inventory Successfully deleted'})
        except Inventory.DoesNotExist:
            return Response({'status':False,'message':'Inventory not found'},status=status.HTTP_400_BAD_REQUEST)
    
class InventoryExcelView(APIView):

    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "invetories"

        export_dir = os.path.join(settings.MEDIA_ROOT, "export", "inventories")
        os.makedirs(export_dir, exist_ok=True)

        file_name = f'Inventories{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        file_path = os.path.join(export_dir, file_name)

        # header row
        sheet.append(["ID", "Product",'Quantity', 'Created At','Last Updated'])
        for cell in sheet[1]:  
            cell.font = Font(bold=True)

        # data rows
        for invetories in Inventory.objects.all():
            sheet.append([invetories.id, invetories.product.name,invetories.quantity,localtime(invetories.created_at).strftime("%Y-%m-%d, %H:%M:%S") or '',localtime(invetories.last_updated).strftime("%Y-%m-%d, %H:%M:%S") or ''])

        workbook.save(file_path)


        file_uri = os.path.join(settings.MEDIA_URL, "export", "inventories", file_name)
        absolute_file_uri = request.build_absolute_uri(file_uri)

        return Response({
            "status": True,
            "file_uri": absolute_file_uri,
            "message": "invetories successfully exported"
        }, status=200)  
        
        
class InventoryReportView(APIView):
    def get(self,request):
        stocks = Inventory.objects.select_related('product','serialno').all()
       
        search = request.query_params.get('search','')
        if search:
            stocks = stocks.filter(Q(product__name__icontains=search) |
                                             Q(serialno__serial_no__icontains=search)
                                             )
        full_stocks = []
        for stock in stocks:
            full_stocks.append({
                'product':stock.product.name,
                'quantity':stock.quantity,
                'serial_no':stock.serialno.serial_no if stock.serialno else '',
                'price':stock.product.retailer_price if stock.product.retailer_price else 0,
                'total_value':stock.value,
            })
        paginator = ListPagination()
        paginated_stocks = paginator.paginate_queryset(full_stocks,request)
        return paginator.get_paginated_response(paginated_stocks)