from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.VendorSerializer import *
from ..models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
from decimal import Decimal, InvalidOperation
import csv
import openpyxl
from openpyxl.styles import Font
from django.http import HttpResponse
from django.utils.timezone import make_naive
from openpyxl.drawing.image import Image as XLImage
import os
from ..pagination import ListPagination
from django.conf import settings


class VendorView(APIView):
    def get(self,request,id=None):
        vendors = ContactModel.objects.filter(contact_role='Vendor').all().order_by('-id')
        search = request.query_params.get('search','')
        if id:
            try:
              vendor = vendors.get(id=id)
              serializer = VendorListSerializer(vendor)
              return Response({'status':True,'data':serializer.data,'message':'Vendor Successfully received'})
            except ContactModel.DoesNotExist:
                return Response({'status':False,'message':'Vendor not available'},status=status.HTTP_400_BAD_REQUEST)
        if search:
            vendors = vendors.filter(Q(name__icontains=search) |
                                     Q(email__icontains=search) |
                                     Q(country__country_name__icontains=search) |
                                     Q(gstin__icontains=search) |
                                     Q(pan_number__icontains=search) |
                                     Q(contact_type__icontains=search)
            )
        paginator = ListPagination()
        paginated_vendors = paginator.paginate_queryset(vendors,request)
        serializer = VendorListSerializer(paginated_vendors,many=True)

        return paginator.get_paginated_response(serializer.data)
    

    def post(self,request):
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Vendor Successfully added'},status=status.HTTP_200_OK)
        return Response({'status':True,'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request,id):
        try:
            vendor = ContactModel.objects.get(id=id)
            serializer = VendorSerializer(vendor,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Vendor Successfully updated'})
            return Response({'status':False,'errors':serializer.errors})
        except ContactModel.DoesNotExist:
            return Response({'status':False,'message':'Vendor not available'},status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self,request,id):
        try:
            vendor = ContactModel.objects.get(id=id)
            vendor.delete()
            return Response({'status':True,'message':'Vendor Successfully deleted'})

        except ContactModel.DoesNotExist:
           return Response({'status':False,'message':'Vendor not available'},status=status.HTTP_400_BAD_REQUEST)        

class Export_vendors_excel(APIView):
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Vendors"


        export_dir = os.path.join(settings.MEDIA_ROOT, "export", "vendors")
        os.makedirs(export_dir, exist_ok=True)
        file_name = f'vendors{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        file_path = os.path.join(export_dir, file_name)

        vendors = ContactModel.objects.filter(contact_role='Vendor',is_active=True)

        sheet.append(["ID", "Name",'Contact Type','Email','Phone No.','GSTIN','PAN NO.','Address'])
        for cell in sheet[1]:  # first row
            cell.font = Font(bold=True)

        # data rows
        for vendor in vendors:
            addresses = "| ".join([ f"{addr.address}, {addr.city}, {addr.state},{addr.country} - {addr.pincode}"for addr in vendor.many_address.all()])
            sheet.append([vendor.id,vendor.name or '',vendor.contact_type or '',vendor.email or '',str(vendor.phone_no) or '',vendor.gstin or '',vendor.pan_number or '',addresses or ''])

        workbook.save(file_path)

        # Generate file URL
        file_uri = os.path.join(settings.MEDIA_URL, "export", "vendors", file_name)
        absolute_file_uri = request.build_absolute_uri(file_uri)

        return Response({
            "status": True,
            "file_uri": absolute_file_uri,
            "message": "Vendor successfully exported"
        }, status=200)