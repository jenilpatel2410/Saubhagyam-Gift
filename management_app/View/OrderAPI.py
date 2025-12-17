from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.OrderSerializer import *
from ..models import *
from user_app.models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
from django.conf import settings
import csv
import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font
import reportlab
import requests
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.utils.timezone import localtime
from ..pagination import ListPagination
from rest_framework.permissions import IsAuthenticated
import json
from num2words import num2words
from management_app.signals import generate_sequence_id


class OrderView(APIView):

    def get(self, request):
        orders = OrderModel.objects.all().order_by('order_type', '-id')

        search = request.query_params.get('search', '')
        user_type = request.query_params.get('type', '')
        filter_value = request.query_params.get('filter', '')
        start_date = request.query_params.get('start_date', '')
        end_date = request.query_params.get('end_date', '')

        role_types = RoleModel.objects.values_list('type', flat=True).distinct()
        role_types_lower = [r.lower() for r in role_types if r is not None]

        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

                # Convert naive → aware based on TIME_ZONE setting
                start_dt = timezone.make_aware(start_dt)
                end_dt = timezone.make_aware(end_dt)

                orders = orders.filter(order_date__range=(start_dt, end_dt))
            except Exception as e:
                print("Date parsing error:", e)

        if filter_value:
            orders = orders.filter(order_status__iexact=filter_value)

        # -------------------------------
        # Role-based filtering
        # -------------------------------
        if user_type in role_types_lower:
            orders = orders.filter(customer__role__type__iexact=user_type)

        if search:
            orders = orders.filter(
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(order_id__icontains=search) |
                Q(final_total__icontains=search) |
                Q(order_date__icontains=search) |
                Q(pay_type__icontains=search)
            )

        paginator = ListPagination()
        paginated_orders = paginator.paginate_queryset(orders, request)
        serializer = OrderSerializer(paginated_orders, many=True, context={'request': request})

        return paginator.get_paginated_response(serializer.data)
    

class OrderDetailsView(APIView):

    def get(self,request,id=None):
        if id:
            try:
                order = OrderModel.objects.get(id=id)
                order_lines = order.orderrelation.all().select_related('product','order')
                
                customer_instance = ContactModel.objects.filter(user=order.customer).first()

                orderdetails = {
                    'order_id': order.order_id,
                    'customer' : f'{order.customer.firm_name}' if order.customer and order.customer.firm_name != "" else f"{order.customer.first_name} {order.customer.last_name}",
                    'customer_id': customer_instance.id if customer_instance else None,
                    'order_date': order.order_date,
                    'status':order.order_status,
                    'product_total':order.product_total,
                    'discount':order.discount,
                    'discount_amt': order.discount_amt,
                    'final_total':order.final_total,
                    'contact_number' :str(order.customer.mobile_no) if order.customer.mobile_no else '',
                    'sales_person': f'{order.sales_person.first_name} {order.sales_person.last_name}' if order.sales_person else '',
                    'pay_type':order.pay_type,
                    'shipping_address':order.shipping_address,
                    'order_type': order.order_type,
                }
                first_line = order_lines.first()
                if not first_line:

                    return Response({
                        "status": True,
                        "data":{'order_details': orderdetails, 'products': []},
                        "message": "No ordered products found for this order.",
                    }, status=status.HTTP_200_OK)
                
                order = first_line.order

                products=[]
                for lines in order_lines:
                    if lines and lines.product:
                        image_obj = ProductImageModel.objects.filter(product=lines.product.id).first()
                    else:
                        image_obj = None
                        
                    products.append({
                        'image' : image_obj.image.url if image_obj else  '-',
                        'id':lines.product.id,
                        'product':lines.product.name if lines.product else '-',
                        'price':lines.selling_price,
                        'item_code':lines.product.item_code if lines.product else '-',
                        'discount':lines.discount,
                        'quantity':lines.quantity,
                        'sub_total':lines.product_total,
                        'stock': Inventory.objects.filter(product=lines.product).first().quantity if Inventory.objects.filter(product=lines.product).exists() else 0
                    })


                return Response({'status':True,'data':{'order_details':orderdetails,'products':products},'message':'Order details retrieved successfully'})   
            except OrderModel.DoesNotExist:
                return Response({'status':False,'message':'Order not found'},status=status.HTTP_400_BAD_REQUEST)
              

    def post(self,request,id=None):
        order_status = request.data.get('order_status','')

        if order_status:
            try:
                order = OrderModel.objects.get(id=id)
                order.order_status = order_status
                order.save()
                return Response({'status':True,'message':'Order status updated successfully'})
            except OrderModel.DoesNotExist:
                return Response({'status':False,'message':'Order not found'},status=status.HTTP_404_NOT_FOUND)           

# def build_pdf(data):
#     from reportlab.lib.pagesizes import A4
#     from reportlab.lib import colors
#     from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
#     from reportlab.lib.styles import getSampleStyleSheet

#     response = HttpResponse(content_type="application/pdf")
#     response["Content-Disposition"] = 'inline; filename="order_invoice.pdf"'

#     doc = SimpleDocTemplate(response, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()

#     # Use default font (Helvetica)
#     styles["Normal"].fontName = "Helvetica"
#     styles["Title"].fontName = "Helvetica-Bold"

#     # Title
#     elements.append(Paragraph("<b>Order INVOICE</b>", styles["Title"]))
#     elements.append(Spacer(1, 12))

#     # Order Details Table (neater than plain text)
#     order = data["order_details"]
#     order_table_data = [
#         ["Order ID", order["id"]],
#         ["Customer", order["customer"]],
#         ["Order Date", order["order_date"]],
#         ["Status", order["status"]],
#     ]

#     order_table = Table(order_table_data, colWidths=[100, 380])
#     order_table.setStyle(TableStyle([
#         ("GRID", (0, 0), (-1, -1), 1, colors.black),
#         ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
#         ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
#     ]))
#     elements.append(order_table)
#     elements.append(Spacer(1, 20))

#     # Product Table
#     products = data["products"]
#     table_data = [["Product", "Item Code", "Price", "Quantity", "Subtotal"]]

#     for p in products:
#         table_data.append([
#             p["product"],
#             p["item_code"] if p["item_code"] else "-",
#             f"Rs. {p['price']:.2f}",
#             str(p["quantity"]),
#             f"Rs. {p['sub_total']:.2f}"
#         ])

#     # Add Grand Total
#     grand_total = sum(float(p["sub_total"]) for p in products)
#     table_data.append(["", "", "", "Grand Total", f"Rs. {grand_total:.2f}"])

#     table = Table(table_data, colWidths=[150, 80, 80, 80, 100])
#     table.setStyle(TableStyle([
#         ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
#         ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
#         ("ALIGN", (0, 0), (-1, -1), "CENTER"),
#         ("GRID", (0, 0), (-1, -1), 1, colors.black),
#         ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
#         ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
#         ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
#     ]))

#     elements.append(table)

#     doc.build(elements)
#     return response



class Order_Pdf_View(APIView):

    def post(self, request):
        order_id = request.data.get('order_id', '')
        comp_id = request.data.get('company_id', '')

        if not order_id:
            return Response({'status': False, 'message': 'Order ID not provided'}, status=400)

        try:
            order = OrderModel.objects.get(id=order_id)

            # --- Order Details ---
            final_total_words = num2words(order.final_total or 0, to='cardinal', lang='en').title() + " Only"
            discount_amount = (order.product_total or 0) - (order.final_total or 0)

            orderdetails = {
                'id': order.order_id,
                'customer': f'{order.customer.first_name} {order.customer.last_name}' if order.customer else '',
                'phone_no': order.customer.mobile_no or '',
                'email': order.customer.email or '',
                'advance_amount': order.advance_amount or 0,
                'shipping_address': order.shipping_address,
                'order_date': order.created_at.strftime("%d-%m-%Y %I:%M %p") if order.created_at else '',
                'remarks': order.remark,
                'status': order.order_status,
                'product_total': order.product_total or 0,
                'discount': order.discount or 0,
                'final_total': order.final_total or 0,
                'final_total_words': final_total_words,
                'discount_amount': discount_amount,
            }

            # --- Products List ---
            qs = OrderLinesModel.objects.filter(order_id=order_id)
            if comp_id:
                qs = qs.filter(product__company_id=comp_id)

            qs = qs.select_related('product')

            products = []
            for line in qs:
                image_obj = ProductImageModel.objects.filter(product=line.product_id).first()
                image_path = os.path.join(settings.MEDIA_ROOT, image_obj.image.name) if image_obj else ''

                products.append({
                    'image': image_path,
                    'product': line.product.name,
                    'unit': line.product.unit,
                    'price': line.selling_price,
                    'item_code': line.product.item_code,
                    'quantity': line.quantity or 0,
                    'discount': line.discount or 0,
                    'sub_total': line.product_total or 0
                })

            # Summary
            grand_total = sum(float(p["sub_total"]) for p in products)
            total_quantity = sum(p["quantity"] for p in products)

            logo_path_uri = os.path.join(settings.MEDIA_URL, "logo", "image.png")
            logo_path = request.build_absolute_uri(logo_path_uri)

            # Employee download tracking
            if request.user.role.type == 'Employee':
                order.is_downloaded = True
                order.save()

            # Generate HTML
            html = render_to_string("invoice_template.html", {
                "order": orderdetails,
                "products": products,
                "grand_total": grand_total,
                "total_quantity": total_quantity,
                "logo_path": logo_path,
            })

            # --- Path to Save PDF ---
            export_dir = os.path.join(settings.MEDIA_ROOT, "export", "sales_invoice_pdf")
            os.makedirs(export_dir, exist_ok=True)

            safe_order_id = str(order.order_id).replace("/", "_").replace("\\", "_")
            filename = f"order_{safe_order_id}.pdf"
            pdf_path = os.path.join(export_dir, filename)
            pdf_url = request.build_absolute_uri(
                f"{settings.MEDIA_URL}export/sales_invoice_pdf/{filename}"
            )

            # --- Write PDF File ---
            with open(pdf_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(html, dest=pdf_file)

            if pisa_status.err:
                return Response({
                    "status": False,
                    "message": "Error generating PDF"
                }, status=500)

            return Response({
                "status": True,
                "file_uri": pdf_url,
                "html": html,
                "message": "Order Print Downloaded Successfully."
            })

        except OrderModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Order not exist'
            }, status=404)
            # return build_pdf(data)

class Export_orders_excel(APIView):
    def get(self,request):
        user_type = request.query_params.get('type','')
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Orders"


        export_dir = os.path.join(settings.MEDIA_ROOT, "export", "orders")
        os.makedirs(export_dir, exist_ok=True)
        if user_type:
            file_name = f'{user_type.lower()}_orders{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        else:
            file_name = f"orders{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = os.path.join(export_dir, file_name)

        orders = OrderModel.objects.all()

        if user_type:
            user_type = user_type.title()
            orders = orders.filter(customer__role__type=user_type)
            sheet.append(["Order ID", "Customer",' Total Price','Date & Time','Payment Status','Order Status'])
            for cell in sheet[1]:  # first row
                cell.font = Font(bold=True)
        else:
            sheet.append(["Order ID", "Customer",' Total Price','Date & Time','Payment Status','Order Status'])
            for cell in sheet[1]:  # first row
                cell.font = Font(bold=True)

        # data rows
        for orders in orders:
            sheet.append([orders.order_id, f'{orders.customer.first_name} {orders.customer.last_name}' if orders.customer else '',orders.final_total, orders.order_date.strftime("%Y-%m-%d") or '', orders.pay_type, orders.order_status or ''])

        workbook.save(file_path)

        # Generate file URL
        file_uri = os.path.join(settings.MEDIA_URL, "export", "orders", file_name)
        absolute_file_uri = request.build_absolute_uri(file_uri)

        return Response({
            "status": True,
            "file_uri": absolute_file_uri,
            "message": "Orders successfully exported"
        }, status=200)
        
        
class OrderCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user_id = user.id
        customer_id = request.data.get("customer_id")
        paid_amount = float(request.data.get("paid_amount", 0))
        order_discount = float(request.data.get("order_discount", 0))

        if not user_id or not customer_id:
            return Response({"status": False, "message": "user_id and customer_id required"})

        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return Response({"status": False, "message": "Invalid user_id"})

        try:
            customer = ContactModel.objects.get(id=customer_id)
            customer = customer.user
        except:
            return Response({"status": False, "message": "Invalid customer_id"})

        products_raw = request.data.get("products", [])
        if not products_raw:
            return Response({"status": False, "message": "Products list cannot be empty"})

        final_total = 0
        product_total = 0
        main_total = 0
        product_info_list = []

        if isinstance(products_raw, str):
            try:
                products = json.loads(products_raw)
            except Exception:
                return Response({"status": False, "message": "Products must be valid JSON"})
        else:
            products = products_raw

        for item in products:
            product_obj = ProductModel.objects.get(id=item["product_id"])
            qty = int(item["quantity"])
            price = float(item["price"])
            discount = float(item.get("discount", 0))
            discount_price = price - (price * discount / 100)

            line_total = discount_price * qty
            final_total += line_total
            product_total += price * qty
            main_total = product_total

            product_info_list.append({
                "product_id": product_obj.id,
                "name": product_obj.name,
                "qty": qty,
                "price": price,
                "discount": discount,
                "discount_price": discount_price
            })

        if order_discount:
            main_total = product_total
            product_total = final_total
            order_discount_amount = final_total * (order_discount / 100)

            final_total = final_total - order_discount_amount
            
        final_total = float(final_total)
        paid_amount = float(paid_amount)

        old_advance = float(customer.advance_amount or 0)
        old_unpaid = float(customer.unpaid_amount or 0)

        order_advance = 0
        order_balance = 0

        if paid_amount >= final_total:
            extra = paid_amount - final_total

            if extra >= old_unpaid:
                extra -= old_unpaid
                old_unpaid = 0
                order_advance = extra  
                is_paid = True
            else:
                old_unpaid -= extra
                order_balance = old_unpaid
                is_paid = False

            customer.advance_amount = old_advance + order_advance
            customer.unpaid_amount = old_unpaid
            customer.save()

        else:
            due = final_total - paid_amount

            if old_advance >= due:
                old_advance -= due
                is_paid = True
                customer.advance_amount = old_advance
                customer.unpaid_amount = old_unpaid
                customer.save()
            else:
                due -= old_advance
                customer.advance_amount = 0
                customer.unpaid_amount = old_unpaid + due
                order_balance = old_unpaid + due
                is_paid = False
                customer.save()

        address = customer.address.first()

        if address and not request.data.get("shipping_address", ""):
            shipping_addr = f"{address.street}, {address.city}, {address.state}, {address.pincode}"
        else:
            shipping_addr = request.data.get("shipping_address", "")

        order = OrderModel.objects.create(
            sales_person=user,
            customer=customer,
            product_info=json.dumps(product_info_list),
            shipping_address=shipping_addr,
            transaction_id=request.data.get("transaction_id", ""),
            main_price=main_total,
            final_total=round(final_total, 2),
            product_total=product_total,
            discount=order_discount,
            discount_amt = order_discount_amount if order_discount else 0,
            remark=request.data.get("remark", ""),
            sale_status="Sales Order",
            order_status=request.data.get("order_status", "pending"),
            order_type=request.data.get("order_type", "Normal"),
            is_paid=is_paid,
            paid_amount=paid_amount,
            advance_amount=order_advance,
            balance_amount=order_balance,
        )
        

        for item in products:
            price = float(item["price"])
            qty = int(item["quantity"])
            discount = float(item.get("discount", 0))

            # Correct discount price calculation PER PRODUCT
            discount_price = price - (price * discount / 100)

            OrderLinesModel.objects.create(
                order=order,
                product_id=item["product_id"],
                quantity=qty,
                selling_price=price,
                discount=discount,
                discount_price=discount_price,
                product_total=discount_price * qty
            )
            
        order.pay_type = "cod"
        order.save()

        lines = OrderLinesModel.objects.filter(order=order)
        serializer = MobileOrderLineSerializer(lines, many=True)

        return Response({
            "status": True,
            "message": "Order placed successfully",
            "order_id": order.id,
            "data": serializer.data
        })
    

    def patch(self,request,id):
        customer_id = request.data.get('customer_id','')

        if not id:
            return Response({'status':False,'message':'Order Id is required'})
        
        try:
          order = OrderModel.objects.get(id=id)
        except OrderModel.DoesNotExist:
            return Response({'status':False,'message':'Order with that id is not available'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        products_raw = request.data.get("products", [])
        previous_total = order.final_total
        if  products_raw:
            if isinstance(products_raw, str):
                try:
                    products = json.loads(products_raw)
                except Exception:
                    return Response({"status": False, "message": "Products must be valid JSON"})
            else:
                products = products_raw

            final_total = 0
            product_total = 0

            for item in products:
                order_line = OrderLinesModel.objects.filter(order=order, product=item["product_id"]).first()

                qty = int(item["quantity"])
                price = float(item["price"])
                discount = float(item.get("discount", 0))
                discount_price = price - (price * discount / 100)
                if order_line is not None:

                    order_line.quantity = qty
                    order_line.selling_price = price
                    order_line.discount = discount
                    order_line.discount_price = discount_price
                    order_line.product_total = discount_price * qty
                    order_line.save()
                else:
                    OrderLinesModel.objects.create(
                        order=order,
                        product_id=item["product_id"],
                        quantity=qty,
                        selling_price=price,
                        discount=discount,
                        discount_price=discount_price,
                        product_total=discount_price * qty
                    )
                line_total = discount_price * qty
                final_total += line_total
                product_total += price * qty
            order.product_total = product_total
            order.final_total = final_total

        if customer_id:
            try:
                customer = ContactModel.objects.get(id=customer_id)
                order.customer = customer.user
            except:
                return Response({"status": False, "message": "Invalid customer_id"})
        

           

        order.shipping_address = request.data.get('shipping_address', order.shipping_address)
        order.order_type = request.data.get('order_type', order.order_type)
        order.pay_type = request.data.get('pay_type', order.pay_type)

        updated_discount = request.data.get('order_discount',None)
        if updated_discount is not None:
            updated_discount = float(updated_discount)
            order.discount = updated_discount
            discount_amount = final_total * (updated_discount / 100)
            order.discount_amt = discount_amount
            order.final_total = final_total - discount_amount
        
        order.order_status = request.data.get('order_status',order.order_status)
        
        customer = order.customer
        unpaid_amount = customer.unpaid_amount
        advance_amount = customer.advance_amount

        if final_total != previous_total:
            if unpaid_amount > 0 and advance_amount == 0.0:
                unpaid_amount = unpaid_amount - previous_total
                unpaid_amount += final_total
            else:
                advance_amount = advance_amount + previous_total
                advance_amount -= final_total
            
            customer.unpaid_amount = unpaid_amount
            customer.advance_amount = advance_amount
            customer.save()
            
        
        order.save()
        return Response({'status':True,'message':'Order updated successfully'})



 



class LatestOrderReferenceNoAPI(APIView):
    
    def get(self, request):
        order_id = generate_sequence_id(OrderModel, "order_id", "SO")
        return Response({'latest_order_id': order_id, 'status': True}, status=status.HTTP_200_OK)
