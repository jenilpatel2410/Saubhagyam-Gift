from rest_framework import serializers
from ..models import PurchaseOrder, PurchaseOrderItem

class MobilePurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'sub_total', 'serial_no', 'description', 'total_price']

class MobilePurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    items = MobilePurchaseOrderItemSerializer(many=True, read_only=True)
    purchase_id = serializers.CharField(read_only=True, default='')
    
    class Meta:
        model = PurchaseOrder
        fields = ['id', 'vendor', 'purchase_id', 'vendor_name', 'order_date', 'purchase_address', 'expected_delivery', 'sub_total', 'order_status', 'status', 'payment_terms', 'items']
