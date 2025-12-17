from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.NewsSerializer import *
from ..models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
import csv
import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font
from ..pagination import ListPagination


class NewsAPI(APIView):

    def get(self,request):
        news = NewsModel.objects.all()
        search = request.query_params.get('search')

        if search:
            news = NewsModel.objects.filter(Q(title__icontains = search) |
                                            Q(description__icontains = search) |
                                            Q(role__type__icontains = search)
                                            )
            
       
        paginator = ListPagination()
        paginated_news = paginator.paginate_queryset(news,request)
        serializer = NewsSerializer(paginated_news,many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        data = request.data
        serializer = NewsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'News Successfully added'})
        
        return Response({'status':False,'errors':serializer.errors})
    
    def patch(self,request,id):
        try:
            news = NewsModel.objects.get(id=id)
            serializer = NewsSerializer(news,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'News Successfully updated'})
            return Response({'status':False,'errors':serializer.errors})
        except BrandModel.DoesNotExist:
            return Response({'status':False,'message':'News not available'},status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self,request,id):
        try:
            news = NewsModel.objects.get(id=id)
            news.delete()
            return Response({'status':True,'message':'News Successfully deleted'})

        except BrandModel.DoesNotExist:
           return Response({'status':False,'message':'News not available'},status=status.HTTP_400_BAD_REQUEST)


class Export_news_excel(APIView):
    
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "News"

        # header row
        sheet.append(["ID", "Title",'Description','Role','Image Url'])
        for cell in sheet[1]:  # first row
            cell.font = Font(bold=True)

        # data rows
        for news in NewsModel.objects.all():
            sheet.append([news.id, news.title,news.description or '',news.role.name if news.role else '',news.image.url if news.image else ''])

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="News.xlsx"'
        workbook.save(response)

        return response
