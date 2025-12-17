from rest_framework.response import Response
from rest_framework import status
from management_app.serializers import *
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


class FeedbackView(APIView):

    def get(self,request):
        feedbacks = FeedbackModel.objects.all()
        search = request.query_params.get('search')
        if search:
            feedbacks = FeedbackModel.objects.filter(Q(name__icontains=search) |
                                               Q(email__icontains=search)|
                                               Q(title__icontains=search) |
                                               Q(description__icontains=search)
                                               )
            
        paginator = ListPagination()
        paginated_feedbacks = paginator.paginate_queryset(feedbacks,request)
        serializer = FeedbackSerializer(paginated_feedbacks,many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        data = request.data
        serializer = FeedbackSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Feedback Successfully added'})
        
        return Response({'status':False,'errors':serializer.errors})
    
    def patch(self,request,id):
        try:
            feedback = FeedbackModel.objects.get(id=id)
            serializer = FeedbackSerializer(feedback,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Feedback Successfully updated'})
            return Response({'status':False,'errors':serializer.errors})
        except FeedbackModel.DoesNotExist:
            return Response({'status':False,'message':'feedback not available'},status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self,request,id):
        try:
            feedback = FeedbackModel.objects.get(id=id)
            feedback.delete()
            return Response({'status':True,'message':'Feedback Successfully deleted'})

        except FeedbackModel.DoesNotExist:
           return Response({'status':False,'message':'Feedback not available'},status=status.HTTP_400_BAD_REQUEST)
        
class Export_feedback_excel(APIView):
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Feedbacks"

        # header row
        sheet.append(["ID", "Name",'Email','Title','Description'])
        for cell in sheet[1]:  # first row
            cell.font = Font(bold=True)


        # data rows
        for feedbacks in FeedbackModel.objects.all():
            sheet.append([feedbacks.id, feedbacks.name, feedbacks.email ,feedbacks.title or '',feedbacks.description or ''])

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="Feedbacks.xlsx"'
        workbook.save(response)

        return response