from django.db.models.functions import TruncMonth,TruncDate
from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from management_app.serializer.PurchaseSerializer import MobilePurchaseOrderItemSerializer, MobilePurchaseOrderSerializer
from management_app.models import PurchaseOrder,PurchaseOrderItem
from collections import defaultdict
from django.db.models import Q
from ..pagination import ListPagination
from xhtml2pdf import pisa
from django.conf import settings
from django.template.loader import get_template
import requests,os
from datetime import datetime

class PurchaseInvoiceView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = ListPagination

    def get(self, request, id=None):
        purchase_invoices = PurchaseOrder.objects.all().order_by('-id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        vendor_id = request.query_params.get('vendor_id')
        is_pdf = request.query_params.get('is_pdf','').lower()
        
        if vendor_id:
            purchase_invoices = purchase_invoices.filter(vendor = vendor_id)
        
        if start_date and end_date:
            purchase_invoices = purchase_invoices.filter(order_date__date__range=[start_date, end_date])

        if id:
            try:
                purchase_invoice = purchase_invoices.get(id=id)
            except PurchaseOrder.DoesNotExist:
                return Response({'status': False, 'message': 'Invoice not found'}, status=status.HTTP_400_BAD_REQUEST)

            purchase_items = PurchaseOrderItem.objects.filter(purchase_order=purchase_invoice).select_related('product')
            purchase_details = []
            for item in purchase_items:
                purchase_details.append({
                    "product": item.product.name,
                    "quantity": item.quantity,
                    "price": float(item.unit_price),
                    "discount" : item.discount,
                    "total": float(item.sub_total),
                    "description": item.description,
                })

            serializer = MobilePurchaseOrderSerializer(purchase_invoice)
            data = serializer.data
            data['product_details'] = purchase_details
            from datetime import datetime
            if is_pdf:
                try:
                    context = {
                        "purchase_id": data.get("purchase_id"),
                        "customer_name": data.get("vendor_name"),
                        "items": data.get("product_details", []),
                        "grand_total": data.get("sub_total", 0),
                        "bank_total": data.get("sub_total", 0),
                        "order_date": datetime.fromisoformat(data.get("order_date")).strftime("%d %b %Y, %I:%M %p"),
                        "heading" : "PURCHASE INVOICE"
                    }
                    template = get_template("sale_purchase_invoicedetail.html")
                    html = template.render(context)

                    # Create export directory
                    export_dir = os.path.join(settings.MEDIA_ROOT, "export", "purchase_invoice_detail_pdf")
                    os.makedirs(export_dir, exist_ok=True)

                    # ✅ Fix for your error — correct datetime import
                    from datetime import datetime
                    file_name = f"purchase_invoice_detail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    file_path = os.path.join(export_dir, file_name)

                    # Generate PDF file
                    with open(file_path, "wb") as pdf_file:
                        pisa_status = pisa.CreatePDF(html, dest=pdf_file)

                    if pisa_status.err:
                        return Response({"status": False, "message": "Error generating PDF"}, status=500)

                    # Return absolute file URI
                    file_uri = os.path.join(settings.MEDIA_URL, "export", "purchase_invoice_detail_pdf", file_name)
                    absolute_file_uri = request.build_absolute_uri(file_uri)

                    return Response({
                        "status": True,
                        "file_uri": absolute_file_uri,
                        "message":"Purchase invoices PDF successfully generated",
                    }, status=200)

                except Exception as e:
                    return Response({
                        "status": False,
                        "message": f"Something went wrong: {str(e)}"
                    }, status=500)

            return Response({'status': True, 'data': data, 'message': 'Invoice details fetched successfully'}, status = status.HTTP_200_OK)

        # List of invoices
        paginator = self.pagination_class()
        all_records = request.query_params.get('all', False)

        if all_records and all_records in ['1', 'true', 'True', True]:
            paginated_invoices = None
        else:
            paginated_invoices = paginator.paginate_queryset(purchase_invoices, request)

        if paginated_invoices is not None:
            serializer = MobilePurchaseOrderSerializer(paginated_invoices, many=True)
            return paginator.get_paginated_response(serializer.data)

        # If "all" is requested, return all without pagination
        serializer = MobilePurchaseOrderSerializer(purchase_invoices, many=True)
        return Response({'status': True, 'data': serializer.data, 'message': 'Invoice list fetched successfully'}, status = status.HTTP_200_OK)


class GroupByPurchaseView(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    filter_backends = [SearchFilter]
    search_fields = ['vendor__name', 'order_status', 'payment_terms','status_choices','vendor__phone_no','vendor__email','vendor__address',]
    
    def get(self, request):
        invoices = PurchaseOrder.objects.all().order_by('-id')

        group_by = request.query_params.get('group_by')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        is_pdf = request.query_params.get('is_pdf','').lower()
        # search = request.query_params.get('search', '')

        if start_date and end_date:
            invoices = invoices.filter(order_date__date__range=[start_date, end_date])

        # if search:
        #     invoices = invoices.filter(Q(vendor__name__icontains=search))
            
        # Grouping logic
        grouped_response = []
        
        if group_by == 'daily_purchase':
            invoices = invoices.annotate(day=TruncDate('order_date'))
            daily_data = defaultdict(list)
            for invoice in invoices:
                day_key = invoice.order_date.strftime("%Y-%m-%d")
                daily_data[day_key].append(invoice)

            for day, orders_list in daily_data.items():
                total_amount = sum(order.sub_total for order in orders_list)
                total_products = PurchaseOrderItem.objects.filter(purchase_order__in=orders_list).aggregate(
                    total_quantity=Sum('quantity')
                )['total_quantity'] or 0
                grouped_response.append({
                    'date': day,
                    'total_amount': float(total_amount),
                    'total_products': total_products,
                    'orders_count': len(orders_list),
                })

        elif group_by == 'monthly_purchase':
            invoices = invoices.annotate(month=TruncMonth('order_date')).order_by('month', '-id')
            monthly_data = defaultdict(list)
            for invoice in invoices:
                month_key = invoice.order_date.strftime("%B %Y")
                monthly_data[month_key].append(invoice)

            for month, orders in monthly_data.items():
                serializer = MobilePurchaseOrderSerializer(orders, many=True)
                total_amount =  sum(sale.sub_total for sale in orders)
                grouped_response.append({
                    "month": month,
                    "invoices": serializer.data,
                    "total_amount":total_amount,
                })

        elif group_by == 'vendor':
            vendor_data = defaultdict(list)
            for invoice in invoices:
                vendor_key = invoice.vendor.name if invoice.vendor else "Unknown"
                vendor_data[vendor_key].append(invoice)

            for vendor_name, orders in vendor_data.items():
                serializer = MobilePurchaseOrderSerializer(orders, many=True)
                total_amount = sum(getattr(sale, "sub_total", 0) or 0 for sale in orders)
                grouped_response.append({
                    "id" : orders[0].vendor.id if orders[0].vendor else None,
                    "vendor": vendor_name,
                    "total": float(total_amount),
                    "invoices": serializer.data,
                })
            
            if is_pdf:
                data = [] 
                try:
                    for d in grouped_response:
                        data.append({
                            "name" : d['vendor'],
                            "bills":len(d['invoices']),
                            "amount":d['total'],
                        })
                    template = get_template("cust_ven_invoice.html")
                    html = template.render({
                        "data": data,
                        "heading":  "Saubhagyam - Vendor Wise Purchase List"
                    })
                    export_dir = os.path.join(settings.MEDIA_ROOT, "export", "vendor_wise_purchase_invoices_pdf")
                    os.makedirs(export_dir, exist_ok=True)

                    # Generate unique file name
                    file_name = f'vendor_wise_purchase_invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                    file_path = os.path.join(export_dir, file_name)

                    # Create the PDF file
                    with open(file_path, "wb") as pdf_file:
                        pisa_status = pisa.CreatePDF(html, dest=pdf_file)

                    # Check for PDF generation errors
                    if pisa_status.err:
                        return Response({"status": False, "message": "Error generating PDF"}, status=500)

                    # Build file URL for download
                    file_uri = os.path.join(settings.MEDIA_URL, "export", "vendor_wise_purchase_invoices_pdf", file_name)
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
            serializer = MobilePurchaseOrderSerializer(invoices, many=True)
            grouped_response = serializer.data
            
        paginator = self.pagination_class()
        all_records = request.query_params.get('all', False)

        if not (all_records and all_records in ['1', 'true', 'True', True]):
            paginated = paginator.paginate_queryset(grouped_response, request)
            return paginator.get_paginated_response(paginated)

        return Response({'status': True, 'data': grouped_response, 'message': 'Grouped invoices fetched successfully'}, status = status.HTTP_200_OK)
