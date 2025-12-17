from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.CategorySerializer import *
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


class BusinessCategoryAPI(APIView):

    def get(self,request):
        categories = BusinessCategoryModel.objects.all()
        search = request.query_params.get('search','')
        if search:
            categories = BusinessCategoryModel.objects.filter(Q(name__icontains=search)
                                                              )
        paginator = ListPagination()
        paginated_categories= paginator.paginate_queryset(categories,request)
        serializer = BusinessCategorySerializer(paginated_categories,many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        data=request.data
        serializer = BusinessCategorySerializer(data=data)  
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Business Category Successfully added'})
        return Response({'status':False,'errors':serializer.errors})
    
    def patch(self,request,id):
        try:
            category = BusinessCategoryModel.objects.get(id=id)
            serializer = BusinessCategorySerializer(category,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Business Category Successfully updated'},status=status.HTTP_200_OK)
            return Response({'status':False,'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        except BusinessCategoryModel.DoesNotExist:
            return Response({'status':False,'message':'Business Category not Available'},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,id):
        try :
            category = BusinessCategoryModel.objects.get(id=id)
            category.delete()
            return Response({'status':True,'message':'Business Category successfully deleted'})
        except BusinessCategoryModel.DoesNotExist:
           return Response({'status':False,'message':'Business Category not available'},status=status.HTTP_400_BAD_REQUEST)
        
    
class Export_business_categories_csv(APIView):
   def get(self,request):
       response = HttpResponse(content_type="text/csv")
       response['content-Disposition'] = 'attachment; filename = "business_categories.csv"'

       writer = csv.writer(response)
       writer.writerow(['ID','Name'])

       for category in BusinessCategoryModel.objects.all():
           writer.writerow([category.id,category.name])

       return response
   

class Export_business_categories_excel(APIView):
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Business Categories"

        # header row
        sheet.append(["ID", "Name"])
        for cell in sheet[1]:  # first row
            cell.font = Font(bold=True)

        # data rows
        for category in BusinessCategoryModel.objects.all():
            sheet.append([category.id, category.name])

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="Business categories.xlsx"'
        workbook.save(response)

        return response


        
    
