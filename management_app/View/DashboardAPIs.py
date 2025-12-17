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
from django.utils import timezone ,dates 


class  DashboardView(APIView):

    def get(self,request):
        data = {
            "total_products" :ProductModel.objects.filter(is_active=True).count(),
            "total_orders": OrderModel.objects.count(), # exclude(order_status='delivered')
            "total_users":ContactModel.objects.filter(is_active=True,user__role__type__in = ['Wholesaler','Retailer']).count(),
            'total_categories':CategoryModel.objects.filter(is_active=True).count()
            # "Retailer Orders" : OrderModel.objects.filter(customer__role__type='Retailer').count()
        }

        return Response({'status':True,'data':data,'message':'Data retreived successfully'})


class GraphView(APIView):

    def get(self, request):
        orders = {}

        today = timezone.now().date()
        
        # Last 7 days including today
        for i in range(7):
            day = today - timezone.timedelta(days=6 - i)   # ensures proper order
            count = OrderModel.objects.filter(created_at__date=day).count()
            orders[day.strftime('%d %b %Y')] = count

        return Response({
            'status': True,
            'data': orders,
            'message': 'Data retrieved successfully'
        })



