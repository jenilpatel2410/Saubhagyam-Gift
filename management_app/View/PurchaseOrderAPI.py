from rest_framework.response import Response
from rest_framework import status
from management_app.serializer.PurchaseOrderSerializer import *
from ..models import *
# from sales_client_app.paginations import WebProductPaginationClass
from django.utils.text import slugify
from rest_framework.views import APIView
from django.db.models import Q
from django.conf import settings
from ..pagination import ListPagination
import csv
import openpyxl
import pandas as pd
from openpyxl.styles import Font
from django.http import HttpResponse
from django.utils.timezone import localtime


class PurchaseOrderView(APIView):
    def get(self,request,id=None):
        purchase_orders = PurchaseOrder.objects.all().order_by('-id')
        search = request.query_params.get('search','')
        if id:
            purchase_orders = PurchaseOrder.objects.get(id=id)
            serializer = PurchaseOrderListSerializer(purchase_orders)
            return Response({'status':True,'data':serializer.data})
            

        if search:
            purchase_orders = purchase_orders.filter(Q(vendor__name__icontains=search) |
                                                      Q(order_status__icontains=search)|
                                                      Q(order_date__icontains = search)

            )
        paginator = ListPagination()
        paginated_purchase_orders = paginator.paginate_queryset(purchase_orders,request)
        serializer = PurchaseOrderListSerializer(paginated_purchase_orders,many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        purchase_items = request.data.get('purchase_items','')
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            purchase_order=serializer.save()
            if purchase_items:
                for item in purchase_items:
                  item['purchase_order'] = purchase_order.id
                  purchase_items_serializer = PurchaseOrderItemSerializer(data=item)
                  if purchase_items_serializer.is_valid():
                      purchase_items_serializer.save()
                  else:
                      return Response({'status':False,'errors':purchase_items_serializer.errors},status=status.HTTP_200_OK)


            return Response({'status':True,'data':serializer.data,'message':'Purchase Order is created'},status=status.HTTP_200_OK)
        return Response({'status':False,'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request,id):
        try:
          purchase_order = PurchaseOrder.objects.get(id=id)
          purchase_items = request.data.get('purchase_items','')
          serializer = PurchaseOrderSerializer(purchase_order,data=request.data,partial=True, context={"request": request})
          if serializer.is_valid():
              purchase_order = serializer.save()


              if purchase_items:
                  for updated_items in purchase_items:
                      p_item_id = updated_items.get('id')
                      updated_items['purchase_order'] = purchase_order.id
                      if p_item_id:
                            p_item= PurchaseOrderItem.objects.get(id=p_item_id)
                            purchase_items_serializer = PurchaseOrderItemSerializer(p_item,data=updated_items,partial=True)
                      else:
                            purchase_items_serializer = PurchaseOrderItemSerializer(data=updated_items,partial=True)
                           
                     
                      if purchase_items_serializer.is_valid():
                          purchase_items_serializer.save()
                      else:
                        return Response({'status':False,'errors':purchase_items_serializer.errors},status=status.HTTP_200_OK)
            
                      
              
              return Response({'status':True,'data':{'order_data':serializer.data},'message':'Purchase Order is updated successfully'},status=status.HTTP_200_OK)
        except PurchaseOrder.DoesNotExist:
            return Response({'status':False,'message':'Purchase Order not available'})
        
    
    def delete(self,request,id):
        try:
          purchase_order = PurchaseOrder.objects.get(id=id)
          purchase_order.delete()
          return Response({'status':True,'message':'Purchase Order is deleted successfully'},status=status.HTTP_200_OK)
        except PurchaseOrder.DoesNotExist:
            return Response({'status':False,'message':'Purchase Order not available'})
        

class PurchaseOrderItemView(APIView):

    def get(self,request,id):
        if id:
            purchased_order_items = PurchaseOrderItem.objects.filter(purchase_order__id=id).order_by('-id')
            serializer = PurchaseOrderItemListSerializer(purchased_order_items,many=True)
            return Response({'status':True,'data':serializer.data,'message':'Purchase Order Items successfully retreived'},status=status.HTTP_200_OK)
        return Response({'status':False,'message':'Order id is required'},status=status.HTTP_400_BAD_REQUEST)
         
    def patch(self,request,id):
        try:
            purchased_order_items = PurchaseOrderItem.objects.get(id=id)
            serializer = PurchaseOrderItemSerializer(purchased_order_items,data=request.data,partial=True,context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'Products Successfully updated'},status=status.HTTP_200_OK)
            return Response({'status':False,'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except PurchaseOrderItem.DoesNotExist:
            return Response({'status':False,'message':'Purchase Order Item  not available'})

    def delete(self,request,id):
        try:
          purchase_order_item = PurchaseOrderItem.objects.get(id=id)
          purchase_order_item.delete()
          return Response({'status':True,'message':'Purchase Order Item is deleted successfully'},status=status.HTTP_200_OK)
        except PurchaseOrderItem.DoesNotExist:
          return Response({'status':False,'message':'Purchase Order Item  not available'})

class Export_purchase_orders_excel(APIView):
    def get(self,request):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Purchase Orders"


        export_dir = os.path.join(settings.MEDIA_ROOT, "export", "purchase orders")
        os.makedirs(export_dir, exist_ok=True)
        file_name = f'purchase_orders{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        file_path = os.path.join(export_dir, file_name)

        purchase_orders = PurchaseOrder.objects.all()

        sheet.append(["ID", "Vendor",'Date & Time','Sub Total','Order Status'])
        for cell in sheet[1]:  # first row
            cell.font = Font(bold=True)

        # data rows
        for orders in purchase_orders:
            sheet.append([orders.id,orders.vendor.name or '',localtime(orders.order_date).strftime("%Y-%m-%d, %H:%M:%S") or '',orders.sub_total or '',orders.order_status or ''])

        workbook.save(file_path)

        # Generate file URL
        file_uri = os.path.join(settings.MEDIA_URL, "export", "purchase orders", file_name)
        absolute_file_uri = request.build_absolute_uri(file_uri)

        return Response({
            "status": True,
            "file_uri": absolute_file_uri,
            "message": "Purchase Orders successfully exported"
        }, status=200)
    

class ImportPurchaseItemsView(APIView):

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        # ✅ Detect file type
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file)
            else:
                return Response({"error": "Unsupported file format"}, status=400)
        except Exception as e:
            return Response({"error": f"Error reading file: {str(e)}"}, status=400)
        
        formatted_data = []
        for _, row in df.iterrows():
            item_code = row.get('ICODE',None)
            quantity = row.get("quantity", 1)
            discount = row.get("Discount", 0)
            
            
            product_name = str(row.get("name")).strip()

            # ✅ Fetch product from DB
            try:
                product = ProductModel.objects.get(item_code=item_code)
            except ProductModel.DoesNotExist:
                continue

            formatted_data.append({
                "product_id":product.id,
                "product": product_name,
                "item_code":product.item_code,
                "quantity": int(quantity),
                "unit_price":int(product.retailer_price),
                "unit": product.unit,
                # "discount": float(discount),
            })

        # serializer = ImportProductSerializer(formatted_data, many=True)
        return Response(formatted_data, status=status.HTTP_200_OK)