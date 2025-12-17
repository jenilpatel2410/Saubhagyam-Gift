from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.CompanySerializer import *
from ..models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from django.conf import settings
from rest_framework.views import APIView
from django.db.models import Q
import csv
import openpyxl
from openpyxl.styles import Font
from django.http import HttpResponse
from ..pagination import ListPagination


class ComapanyView(APIView):
    
    def get(self,request):
        company = CompanyModel.objects.all()
        search = request.query_params.get('search','')
        if search:
            company = CompanyModel.objects.filter(Q(name__icontains=search) |
                                                  Q(code__icontains=search) |
                                                  Q(address__iontains=search) |
                                                  Q(email__icontains=search) |
                                                  Q(gstin__icontains=search) |
                                                  Q(pan_number__icontains=search) 
                                                  )
        paginator = ListPagination()
        paginated_companies = paginator.paginate_queryset(company,request)
        serializer = CompanyListSerializer(paginated_companies,many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Company saved Successfully'})
        
        return Response({'status':True,'errors':serializer.errors})
    
    def patch(self,request,id):
        try:
            company = CompanyModel.objects.get(id=id)
            serializer = CompanySerializer(company,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Company Successfully updated'})
            return Response({'status':False,'errors':serializer.errors})
        except CompanyModel.DoesNotExist:
            return Response({'status':False,'message':'Company not available'},status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self,request,id):
        try:
            company = CompanyModel.objects.get(id=id)
            company.delete()
            return Response({'status':True,'message':'Company Successfully deleted'})

        except CompanyModel.DoesNotExist:
           return Response({'status':False,'message':'Company not available'},status=status.HTTP_400_BAD_REQUEST)
        
class Export_companies_excel(APIView):
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Companies"

        export_dir = os.path.join(settings.MEDIA_ROOT, "export", "companies")
        os.makedirs(export_dir, exist_ok=True)

        file_name = f'companies{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        file_path = os.path.join(export_dir, file_name)

        # header row
        sheet.append(["ID", "Name",'Code'])
        for cell in sheet[1]:  
            cell.font = Font(bold=True)

        # data rows
        for companies in CompanyModel.objects.all():
            sheet.append([companies.id, companies.name,companies.code])

        workbook.save(file_path)


        file_uri = os.path.join(settings.MEDIA_URL, "export", "companies", file_name)
        absolute_file_uri = request.build_absolute_uri(file_uri)

        return Response({
            "status": True,
            "file_uri": absolute_file_uri,
            "message": "Companies successfully exported"
        }, status=200)
