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


class InquiryView(APIView):

    def get(self,request):
        inquiries = InquiryModel.objects.all()
        search = request.query_params.get('search')
        if search:
            inquiries = InquiryModel.objects.filter(Q(name__first_name__icontains=search) |
                                                Q(name__last_name__icontains=search) |
                                               Q(product__name__icontains=search)|
                                               Q(quantity__icontains=search) |
                                               Q(description__icontains=search) |
                                               Q(status__icontains=search)
                                               )
            
        paginator = ListPagination()
        paginated_inquiries = paginator.paginate_queryset(inquiries,request)
        serializer = InquirySerializer(paginated_inquiries,many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        data = request.data
        serializer = InquirySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Inquiry Successfully added'})
        
        return Response({'status':False,'errors':serializer.errors})
    
    def patch(self,request,id):
        try:
            inquiry = InquiryModel.objects.get(id=id)
            serializer = InquirySerializer(inquiry,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Inquiry Successfully updated'})
            return Response({'status':False,'errors':serializer.errors})
        except InquiryModel.DoesNotExist:
            return Response({'status':False,'message':'Inquiry not available'},status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self,request,id):
        try:
            inquiry = InquiryModel.objects.get(id=id)
            inquiry.delete()
            return Response({'status':True,'message':'Inquiry Successfully deleted'})

        except InquiryModel.DoesNotExist:
           return Response({'status':False,'message':'Inquiry not available'},status=status.HTTP_400_BAD_REQUEST)

class Export_inquiry_excel(APIView):
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Inquiries"

        # header row
        sheet.append(["ID", "Name",'Product Name','Quantity','Description','Status'])
        for cell in sheet[1]:  # first row
            cell.font = Font(bold=True)


        # data rows
        for inquiries in InquiryModel.objects.all():
            sheet.append([inquiries.id, f'{inquiries.name.first_name} {inquiries.name.last_name} ',inquiries.product.name if inquiries.product else '',inquiries.quantity or '',inquiries.description or '',inquiries.status or ''])

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="Inquiries.xlsx"'
        workbook.save(response)

        return response
