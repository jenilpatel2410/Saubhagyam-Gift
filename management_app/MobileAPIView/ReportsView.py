from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.SalesSerializer import *
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
from django.db.models.functions import TruncMonth,TruncDate
from django.db.models.functions import Coalesce,NullIf
from django.db.models import Value, Sum, Count,FloatField,Max, F, Func, CharField
from collections import defaultdict
from rest_framework.permissions import IsAuthenticated
from ..pagination import ListPagination
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
from django.template.loader import get_template
import requests,math



class CustomerSalesReportView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = ListPagination

    def get(self,request):
        search = request.query_params.get('search','').lower()
        orders = OrderModel.objects.all()
        customer_reports = (orders.filter(sale_status='Sales Order').exclude(order_status='cancelled')
                            .values('customer')
                            .annotate(total_amount=Coalesce(Sum(NullIf('final_total',float('nan'))), 0,output_field=FloatField()),
                                      total_orders=Count('id'),
                                       last_order_date=Func(
                                                Max('order_date'),
                                                Value('YYYY-MM-DD HH24:MI:SS'),
                                                function='TO_CHAR',
                                                output_field=CharField()
                                            ))
                            .order_by('-last_order_date'))
        if search:
            filtered_reports = []
            for cust in customer_reports:
                customer = UserModel.objects.filter(id=cust['customer']).first()
                customer_name = f'{customer.first_name} {customer.last_name}' if customer else ""
                email = customer.email if customer and customer.email else ""
                mobile_no = str(customer.mobile_no) if customer else ""

                if (search in customer_name.lower() or
                    search in email.lower() or
                    search in mobile_no.lower()):
                    filtered_reports.append(cust)
            customer_reports = filtered_reports


        for cust in customer_reports:
            customer = UserModel.objects.filter(id=cust['customer']).first()
            cust['customer_name'] = f'{customer.first_name} {customer.last_name}' if customer else ""
            cust['email'] = customer.email if customer else ""
            cust['mobile_no'] = str(customer.mobile_no) if customer else ""
            
            order_info = (orders.filter(customer=cust['customer'],sale_status='Sales Order').exclude(order_status='cancelled'))
            order_details = []

            if order_info:
                for order in order_info:
                    order_details.append({
                        'order_id': order.order_id,
                        'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'final_total': 0 if (order.final_total is None or math.isnan(order.final_total)) else order.final_total,
                        'order_status': order.order_status,
                    })
            
            cust['order_details'] = order_details

            del cust['customer']
        customer_reports = list(customer_reports)

        new_customers = sum(1 for c in customer_reports if c['total_orders'] == 1)
        returned_customers = sum(1 for c in customer_reports if c['total_orders'] > 1)

        

        paginator = self.pagination_class() 
        result_page = paginator.paginate_queryset(customer_reports, request)
        response =  paginator.get_paginated_response(result_page)  
        response.data['new_customers'] = new_customers
        response.data['returned_customers'] = returned_customers
        return response   
    

class PurchaseReportView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = ListPagination

    def get(self,request):
        search = request.query_params.get('search','').lower()
        purchases = PurchaseOrder.objects.all()
        purchase_reports = (purchases.filter(order_status='Purchase Order')
                            .values('vendor')
                            .annotate(total_purchase=Sum('sub_total'),
                                      total_orders=Count('id'),
                                       last_purchase_date=Func(
                                                Max('order_date'),
                                                 Value('YYYY-MM-DD HH24:MI:SS'),
                                                function='TO_CHAR',
                                                output_field=CharField()
                                            ))
                            .order_by('-last_purchase_date'))
        if search:
            filtered_reports = []
            for cust in purchase_reports:
                vendor = ContactModel.objects.filter(id=cust['vendor']).first()
                vendor_name = vendor.name if vendor else ""
                email = vendor.email if vendor and vendor.email  else ""   
                mobile_no = str(vendor.phone_no) if vendor else ""
                if (search in vendor_name.lower() or
                    search in email.lower() or
                    search in mobile_no.lower()):
                    filtered_reports.append(cust)
                purchase_reports = filtered_reports

             

        for cust in purchase_reports:
            vendor = ContactModel.objects.filter(id=cust['vendor']).first()
            cust['vendor_name'] = vendor.name if vendor else ""
            cust['email'] = vendor.email if vendor else ""
            cust['mobile_no'] = str(vendor.phone_no) if vendor else ""

            purchase_info = (purchases.filter(vendor=cust['vendor'],order_status='Purchase Order'))
            purchase_details = []

            for purchase in purchase_info:
                purchase_details.append({
                    'order_id': purchase.purchase_id,
                    'order_date': purchase.order_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'final_total': purchase.sub_total,
                    'order_status': purchase.order_status,
                })
            
            cust['purchase_details'] = purchase_details

            del cust['vendor']
        paginator = self.pagination_class() 
        result_page = paginator.paginate_queryset(purchase_reports, request)
        return paginator.get_paginated_response(result_page)    

class AccountsReceivableReportView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = ListPagination

    def get(self,request):
        search = request.query_params.get('search','').lower()
        payments = OrderModel.objects.filter(sale_status='Sales Order').exclude(order_status='cancelled').select_related('customer')
        payment_reports = (payments.values('customer')
                           .filter(customer__role__type__in = ['Retailer','Wholesaler'],customer__unpaid_amount__gt=0)
                           .annotate(total_amount = Coalesce(Sum(NullIf('final_total',float('nan'))), 0,output_field=FloatField()),
                                     total_paid_amount = F('total_amount') - F('customer__unpaid_amount'),
                                     total_unpaid_amount = F('customer__unpaid_amount'),
                                    last_order_date=Func(
                                                Max('order_date'),
                                                 Value('YYYY-MM-DD, HH24:MI:SS'),
                                                function='TO_CHAR',
                                                output_field=CharField()
                                            )
                                    )
                            .order_by('-last_order_date')   
                             )
        
        
        if search:
            filtered_reports = []
            for payment in payment_reports:
                customer = UserModel.objects.filter(id=payment['customer']).first()
                customer_name = f'{customer.first_name} {customer.last_name}' if customer else ""
                email = customer.email if customer else ""
                mobile_no =str(customer.mobile_no) if customer else ""
                if (search in customer_name.lower() or
                    search in email.lower() or 
                    search in mobile_no.lower()):
                    filtered_reports.append(payment)
            payment_reports = filtered_reports

     
        for report in payment_reports:
            customer = UserModel.objects.filter(id=report['customer']).first()
            report['customer_name'] = f'{customer.first_name} {customer.last_name}' if customer else ""
            report['email'] =  customer.email if customer else ""
            report['mobile_no'] = str(customer.mobile_no) if customer else ""
            
            payment_info = payments.filter(customer=customer).all()
            paymemt_details = []
            for payment in payment_info:
                paymemt_details.append({
                    "order_id":payment.order_id if payment.order_id else '',
                    "payment_datetime":payment.order_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "amount":payment.final_total,
                    "payment_mode":payment.pay_type
                })
            report['payment_details'] = paymemt_details
            del report['customer']

        paginator = self.pagination_class() 
        result_page = paginator.paginate_queryset(payment_reports, request)
        return paginator.get_paginated_response(result_page) 
    

class AccountsPayableReportView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = ListPagination

    def get(self,request):
        search = request.query_params.get('search','').lower()
        payments = OrderModel.objects.filter(sale_status='Sales Order').exclude(order_status='cancelled').select_related('customer')
        payment_reports = (payments.values('customer')
                           .filter(customer__role__type__in = ['Retailer','Wholesaler'],customer__advance_amount__gt=0)
                           .annotate(total_amount = Coalesce(Sum(NullIf('final_total',float('nan'))), 0,output_field=FloatField()),
                                     total_unpaid_amount = F('customer__advance_amount'),  #total_payable_amount_to_customer
                                     total_paid_amount = F('total_amount') + F('customer__advance_amount'),
                                    last_order_date=Func(
                                                Max('order_date'),
                                                 Value('YYYY-MM-DD, HH24:MI:SS'),
                                                function='TO_CHAR',
                                                output_field=CharField()
                                            )
                                    )
                            .order_by('-last_order_date')   
                             )
        
        
        if search:
            filtered_reports = []
            for payment in payment_reports:
                customer = UserModel.objects.filter(id=payment['customer']).first()
                customer_name = f'{customer.first_name} {customer.last_name}' if customer else ""
                email = customer.email if customer else ""
                mobile_no =str(customer.mobile_no) if customer else ""
                if (search in customer_name.lower() or
                    search in email.lower() or 
                    search in mobile_no.lower()):
                    filtered_reports.append(payment)
            payment_reports = filtered_reports

     
        for report in payment_reports:
            customer = UserModel.objects.filter(id=report['customer']).first()
            report['customer_name'] = f'{customer.first_name} {customer.last_name}' if customer else ""
            report['email'] =  customer.email if customer else ""
            report['mobile_no'] = str(customer.mobile_no) if customer else ""
            
            payment_info = payments.filter(customer=customer).all()
            paymemt_details = []
            for payment in payment_info:
                paymemt_details.append({
                    "order_id":payment.order_id if payment.order_id else '',
                    "payment_datetime":payment.order_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "amount":payment.final_total,
                    "payment_mode":payment.pay_type
                })
            report['payment_details'] = paymemt_details
            del report['customer']

        paginator = self.pagination_class() 
        result_page = paginator.paginate_queryset(payment_reports, request)
        return paginator.get_paginated_response(result_page)            
            
class HighValueCustomerView(APIView):
    pagination_class = ListPagination 
    # permission_classes = [IsAuthenticated]
      
    def get(self,request):
        search = request.query_params.get('search','').lower()
        order_details = OrderModel.objects.filter(sale_status='Sales Order').exclude(order_status='cancelled').select_related('customer')
        users = (order_details.values('customer')
        .annotate(total_orders=Count('id'))
        .order_by('-total_orders'))
         
        customer_details = {}
        for user in users:
            customer = UserModel.objects.filter(id=user['customer']).first()
            if customer is not None:
                customer_details[customer.id]= customer
            else:
                continue
                  
        if search:
            filtered_users = []
            for user in users:
                customer = customer_details.get(user['customer'])
                customer_name = f'{customer.first_name} {customer.last_name}' if customer else ""
                email = customer.email if customer else ""
                mobile_no = str(customer.mobile_no) if customer else ""
                if (search in customer_name.lower() or
                    search in email.lower() or 
                    search in mobile_no.lower()):
                    filtered_users.append(user)
            users = filtered_users

        for user in users:               
            customer = customer_details.get(user['customer'])
            user['customer_name'] = f'{customer.first_name} {customer.last_name}' if customer else ""
            user['email'] =  customer.email if customer else ""
            user['mobile_no'] = str(customer.mobile_no) if customer else ""
            del user['customer']
        
        paginator = self.pagination_class() 
        result_page = paginator.paginate_queryset(users, request)   
        return paginator.get_paginated_response(result_page)