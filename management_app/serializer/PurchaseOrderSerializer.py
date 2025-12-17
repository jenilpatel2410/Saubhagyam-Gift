from rest_framework import serializers
from ..models import *
from user_app.serializers import *


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    vendor = serializers.CharField(source='vendor.name',default='')
    order_date = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S")
    purchase_address = serializers.SerializerMethodField()

    def get_purchase_address(self,obj):
        if obj.purchase_address:
            return AddressSerializerForCreate(obj.purchase_address).data

        return {}

    class Meta:
        model = PurchaseOrder
        fields = ['id','purchase_id','vendor','order_date','sub_total','discount','discount_price','final_total','order_status','purchase_address']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ['id','vendor','order_date','expected_delivery','order_status','sub_total','discount','discount_price','final_total','purchase_address']
    

class PurchaseOrderItemListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name',default='')
    unit = serializers.CharField(source='product.unit',default='')
    item_code = serializers.CharField(source='product.item_code',default='')
    serial_no = serializers.CharField(source='serial_no.serial_no',default='')
   


    class Meta:
        model = PurchaseOrderItem
        fields = ['id','product','product_name','item_code','quantity','unit','unit_price','discount','discount_price','sub_total','serial_no']


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
   
        

    class Meta:
        model = PurchaseOrderItem
        fields = ['id','purchase_order','product','quantity','unit_price','discount','discount_price','sub_total','serial_no']