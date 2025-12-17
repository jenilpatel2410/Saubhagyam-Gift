from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.BrandSerializer import *
from ..models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
import csv
import openpyxl
from openpyxl.styles import Font
from django.http import HttpResponse
from ..pagination import ListPagination
from django.conf import settings


class BrandAPI(APIView):

    def get(self,request):
        brands = BrandModel.objects.all()
        search = request.query_params.get('search')
        if search:
            brands = BrandModel.objects.filter(Q(name__icontains=search) |
                                               Q(number__icontains=search)|
                                               Q(description__icontains=search))
        paginator = ListPagination()
        paginated_brands = paginator.paginate_queryset(brands,request)
        serializer = BrandSerializer(paginated_brands,many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        data = request.data
        serializer = BrandSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Brand Successfully added'})
        
        return Response({'status':False,'errors':serializer.errors})
    
    def patch(self,request,id):
        try:
            brand = BrandModel.objects.get(id=id)
            serializer = BrandSerializer(brand,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Brand Successfully updated'})
            return Response({'status':False,'errors':serializer.errors})
        except BrandModel.DoesNotExist:
            return Response({'status':False,'message':'Brand not available'},status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self,request,id):
        try:
            brand = BrandModel.objects.get(id=id)
            brand.delete()
            return Response({'status':True,'message':'Brand Successfully deleted'})

        except BrandModel.DoesNotExist:
           return Response({'status':False,'message':'Brand not available'},status=status.HTTP_400_BAD_REQUEST)
           

class Export_brand_csv(APIView):
   def get(self,request):
       response = HttpResponse(content_type="text/csv")
       response['content-Disposition'] = 'attachment; filename = "brands.csv"'

       writer = csv.writer(response)
       writer.writerow(['ID','Name','Image Url','Description'])

       for brands in BrandModel.objects.all():
           writer.writerow([brands.id,brands.name,brands.image.url if brands.image else '',brands.description])

       return response
   

class Export_brand_excel(APIView):
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Brands"

        export_dir = os.path.join(settings.MEDIA_ROOT, "export", "brands")
        os.makedirs(export_dir, exist_ok=True)

        file_name = f'brands.xlsx'
        file_path = os.path.join(export_dir, file_name)

        # header row
        sheet.append(["ID", "Name",'Description'])
        for cell in sheet[1]:  
            cell.font = Font(bold=True)

        # data rows
        for brands in BrandModel.objects.all():
            sheet.append([brands.id, brands.name,brands.description or ''])

        workbook.save(file_path)


        file_uri = os.path.join(settings.MEDIA_URL, "export", "brands", file_name)
        absolute_file_uri = request.build_absolute_uri(file_uri)

        return Response({
            "status": True,
            "file_uri": absolute_file_uri,
            "message": "Brands successfully exported"
        }, status=200)
