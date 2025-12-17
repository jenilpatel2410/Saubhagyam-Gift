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
from django.db.models.functions import Coalesce
from django.db.models import Value, Sum
from collections import defaultdict
from rest_framework.permissions import IsAuthenticated
from ..pagination import ListPagination
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
from django.template.loader import get_template
import requests

class SalesView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination

    def get(self,request,id=None):
        sales_invoices = OrderModel.objects.filter(sale_status='Sales Order').exclude(order_status='cancelled').order_by('-id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        customer_id = request.query_params.get('customer_id')
        received_id = request.query_params.get('received_id')
        is_draft = request.query_params.get('is_draft', 'false').lower()  # default false
        is_pdf = request.query_params.get('is_pdf', '').lower()
        search = request.query_params.get('search','')

        # 🔹 Apply is_draft filter dynamically
        if is_draft in ['1', 'true', 'yes', True]:
            sales_invoices = sales_invoices.filter(is_draft=True)
        else:
            sales_invoices = sales_invoices.filter(is_draft=False)
            
        if search:
            sales_invoices = sales_invoices.filter(Q(customer__first_name__icontains=search) |
                                                    Q(customer__last_name__icontains=search) |
                                                    Q(order_id__icontains=search) 
                                                    )
        
        if customer_id:
            sales_invoices = sales_invoices.filter(customer = customer_id)
            
        if received_id:
            sales_invoices = sales_invoices.filter(sales_person=received_id)
            
        if start_date or end_date:
            sales_invoices = sales_invoices.filter(order_date__range=(start_date,end_date))
            
        if id:
            sales_details=[]
            sd = OrderLinesModel.objects.filter(order__id=id).select_related('product')
            sales_invoices = sales_invoices.get(id=id)
            serializer = SalesInvoiceListSerializer(sales_invoices)
            for sale in sd:
                effective_price = sale.selling_price - (sale.selling_price * sale.discount / 100)
                total = effective_price * sale.quantity
                
                sales_details.append({
                    "product":sale.product.name,
                    "price":sale.selling_price,
                    "discount":sale.discount,
                    "quantity":sale.quantity,
                    "total": round(total, 2),
                })

            data = serializer.data
            data['product_details'] = sales_details

            if is_pdf:
                try:
                    context = {
                        "order_id": data.get("order_id"),
                        "customer_name": data.get("customer"),
                        "items": data.get("product_details", []),
                        "grand_total": data.get("final_total", 0),
                        "bank_total": data.get("final_total", 0),
                        "order_date": data.get("order_date", 0),
                        "heading":'SALES INVOICE'
                    }
                    template = get_template("sale_purchase_invoicedetail.html")
                    html = template.render(context)

                    # Create export directory
                    export_dir = os.path.join(settings.MEDIA_ROOT, "export", "sales_invoice_pdf")
                    os.makedirs(export_dir, exist_ok=True)

                    # ✅ Fix for your error — correct datetime import
                    from datetime import datetime
                    file_name = f"sales_invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    file_path = os.path.join(export_dir, file_name)

                    # Generate PDF file
                    with open(file_path, "wb") as pdf_file:
                        pisa_status = pisa.CreatePDF(html, dest=pdf_file)

                    if pisa_status.err:
                        return Response({"status": False, "message": "Error generating PDF"}, status=500)

                    # Return absolute file URI
                    file_uri = os.path.join(settings.MEDIA_URL, "export", "sales_invoice_pdf", file_name)
                    absolute_file_uri = request.build_absolute_uri(file_uri)

                    return Response({
                        "status": True,
                        "file_uri": absolute_file_uri,
                        "message":"Sales invoices PDF successfully generated",
                    }, status=200)

                except Exception as e:
                    return Response({
                        "status": False,
                        "message": f"Something went wrong: {str(e)}"
                    }, status=500)

            return Response({'status':True,'data':data,'message':'Invoice List Successfully received'},status = status.HTTP_200_OK)
        
        paginator = self.pagination_class()
        all_records = request.query_params.get('all', False)

        if all_records and all_records in ['1', 'true', 'True', True]:
            paginated_invoices = None
        else:
            paginated_invoices = paginator.paginate_queryset(sales_invoices, request)

        if paginated_invoices is not None:
            serializer = SalesInvoiceListSerializer(paginated_invoices, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SalesInvoiceListSerializer(sales_invoices,many=True)
        return Response({'status':True,'data':serializer.data,'message':'Invoice List Successfully received'},status = status.HTTP_200_OK)
    

class GroupBySalesView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    
    def get(self,request):
        sales_invoice = OrderModel.objects.filter(sale_status='Sales Order').order_by('-id')
        group_by = request.query_params.get('group_by')
        start_date = request.query_params.get('start_date','')
        end_date = request.query_params.get('end_date','')
        search = request.query_params.get('search','')
        is_pdf = request.query_params.get('is_pdf','').lower()
        # print(start_date)
        # print(end_date)
        # print(group_by,'---------')

        if start_date and end_date:
            sales_invoice = sales_invoice.filter(order_date__range=(start_date, end_date))

        if search:
            sales_invoice = sales_invoice.filter(Q(customer__first_name__icontains=search) |
                                                    Q(customer__last_name__icontains=search) |
                                                    Q(order_id__icontains=search) 
                                                    )

        # if group_by == 'daily_sales':
        #     sales_invoice = sales_invoice.annotate(day=TruncDate('order_date')).order_by('-id')
        #     daily_data = defaultdict(list)

        #     for sale in sales_invoice:
        #         day_key = sale.order_date.strftime("%Y-%m-%d")
        #         daily_data[day_key].append(sale)

        #     for day, orders_in_day in daily_data.items():
        #         total_amount = sum(sale.final_total for sale in orders_in_day)
        #         total_sales = OrderLinesModel.objects.filter(product_order__in=orders_in_day).aggregate(
        #             total_quantity=Sum('quantity')
        #         )['total_quantity'] or 0
                
        #         grouped_response.append({
        #             "date": day,
        #             "total_sales": total_sales,
        #             "total_amount": float(total_amount),
        #             "orders_count": len(orders_in_day)
        #         })
        grouped_response = [] 
        
        if group_by == 'daily_sales':
            # order_date is DateField; no need to truncate
            sales_invoice = sales_invoice.order_by('-order_date')
            
            # Group sales by day (store IDs only)
            daily_data = defaultdict(list)
            for sale in sales_invoice:
                day_key = sale.order_date.strftime("%Y-%m-%d")
                daily_data[day_key].append(sale.id)  # store IDs, not objects

            for day_str, order_ids in daily_data.items():
                # Aggregate total amount from OrderModel
                total_amount = OrderModel.objects.filter(id__in=order_ids).aggregate(
                    total_amount=Coalesce(Sum('final_total'), Value(0), output_field=models.FloatField())
                )['total_amount'] 
                
                if isinstance(total_amount, float) and total_amount != total_amount:  # NaN check
                    total_amount = 0

                # Aggregate total quantity from OrderLinesModel
                total_sales = OrderLinesModel.objects.filter(
                    order_id__in=order_ids
                ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

                grouped_response.append({
                    "date": day_str,
                    "total_products_sales": total_sales,
                    "total_amount": float(total_amount),
                    "orders_count": len(order_ids)
                })

        elif group_by == 'monthly_sales' :
            
        
            sales_invoice = (sales_invoice.annotate(month=TruncMonth("order_date")).order_by("month", "-id"))
                
            monthly_data = defaultdict(list)
            for sale in sales_invoice:
                month_key = sale.order_date.strftime("%B %Y")  
                monthly_data[month_key].append(sale)

            grouped_response = []
            
            for month, orders_in_month in monthly_data.items():
                serializer =  GroupBySalesSerializer(orders_in_month,many=True) 
                total_amount =  Coalesce(sum(sale.final_total for sale in orders_in_month), Value(0), output_field=models.FloatField) or 0
                grouped_response.append({
                    "month":month,
                    "invoices" : serializer.data,
                    "total_amount":total_amount,
                })
        elif group_by == 'customer' :

            customer_data=defaultdict(list)
            for sale in sales_invoice:
                if sale.customer :
                    cust_key = f'{sale.customer.first_name} {sale.customer.last_name}' 
                    cust_id = sale.customer.id 
                else :
                    'Not Known'
                customer_data[cust_key].append(sale)

            grouped_response = []
                
            for cust, sales_order in customer_data.items():
                serializer =  GroupBySalesSerializer(sales_order,many=True) 
                total_amount = sum(getattr(sale, "final_total", 0) or 0 for sale in sales_order)
                grouped_response.append({
                    "id" : sales_order[0].customer.id if sales_order[0].customer else None,
                    "customer":cust,
                    "total": float(total_amount),
                    "invoices" : serializer.data,
                })  
            
            if is_pdf:
                data = [] 
                try:
                    for d in grouped_response:
                        data.append({
                            "name" : d['customer'],
                            "bills":len(d['invoices']),
                            "amount":d['total'],
                        })
                    template = get_template("cust_ven_invoice.html")
                    html = template.render({
                        "data": data,
                        "heading":  "Saubhagyam - Customer Wise Sales List"
                    })
                    export_dir = os.path.join(settings.MEDIA_ROOT, "export", "customer_wise_sales_invoices_pdf")
                    os.makedirs(export_dir, exist_ok=True)

                    # Generate unique file name
                    file_name = f'customer_wise_sales_invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                    file_path = os.path.join(export_dir, file_name)

                    # Create the PDF file
                    with open(file_path, "wb") as pdf_file:
                        pisa_status = pisa.CreatePDF(html, dest=pdf_file)

                    # Check for PDF generation errors
                    if pisa_status.err:
                        return Response({"status": False, "message": "Error generating PDF"}, status=500)

                    # Build file URL for download
                    file_uri = os.path.join(settings.MEDIA_URL, "export", "customer_wise_sales_invoices_pdf", file_name)
                    absolute_file_uri = request.build_absolute_uri(file_uri)

                    # Success response
                    return Response({
                        "status": True,
                        "file_uri": absolute_file_uri,
                        "message": "Sales invoices PDF successfully generated"
                    }, status=200)

                except Exception as e:
                    return Response({
                        "status": False,
                        "message": f"Something went wrong: {str(e)}"
                    }, status=500)


        
        else:
            serializer = GroupBySalesSerializer(sales_invoice,many=True)
            grouped_response =  serializer.data

        paginator = self.pagination_class()
        all_records = request.query_params.get('all', False)

        if not (all_records and all_records in ['1', 'true', 'True', True]):
            paginated = paginator.paginate_queryset(grouped_response, request)
            return paginator.get_paginated_response(paginated)
        
        return Response({'status': True,
                         'data': grouped_response,
                         'message' : 'Sales Invoices Successfully Received'},status = status.HTTP_200_OK)
            