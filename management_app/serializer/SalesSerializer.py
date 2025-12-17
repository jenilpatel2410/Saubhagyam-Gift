from rest_framework import serializers
from ..models import *
from user_app.serializers import *
from .OrderSerializer import MobileOrderLineSerializer,OrderModel
from management_app.serializer.ContactSerializer import CustomerSerializer
class SalesInvoiceListSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    customer_detail = CustomerSerializer(source='customer',read_only=True)

    def get_customer(self,obj):
        if obj.customer:
            return f'{obj.customer.first_name} {obj.customer.last_name}'
        
        return ''
    class Meta:
        model = OrderModel
        fields = ['id','order_id','customer','customer_detail','final_total','order_date','advance_amount','balance_amount']

class GroupBySalesSerializer(serializers.ModelSerializer):
    
    product_details = serializers.SerializerMethodField()

    def get_product_details(self,obj):
        product_details = OrderLinesModel.objects.filter(order=obj)
        details=[]  
        for product in product_details:
            details.append({
                "product":product.product.name if product.product else '',
                "price":product.selling_price if product.selling_price else 0,
                "discount":product.discount if product.discount else 0,
                "quantity":product.quantity if product.quantity else 0,
            })
        return details

    class Meta:
        model = OrderModel
        fields = ['id','order_id','customer','advance_amount','balance_amount','product_details','final_total','order_date']