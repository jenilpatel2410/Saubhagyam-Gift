from rest_framework import serializers
from ..models import *
from django.db.models import Sum


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name',default='',read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)
    last_updated = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)

    def create(self,validated_data):
        product = validated_data.get('product')
        quantity = validated_data.get('quantity',0)

        inventory = Inventory.objects.filter(product=product)
        if inventory.exists():
            inventory = inventory.first()
            inventory.quantity += quantity
            inventory.save()
            return inventory
        else:
            return super().create(validated_data)
        
    class Meta:
        model = Inventory
        fields = ['id','product','product_name','quantity','serialno','created_at','last_updated']

class MobileInventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name',default='')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    last_updated = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    ordered_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = ['id','product','product_name','quantity','serialno','created_at','last_updated','ordered_quantity']

    def get_ordered_quantity(self, obj):
        # Sum of all quantities in order lines for this product
        result = OrderLinesModel.objects.filter(product=obj.product).aggregate(total_qty=Sum('quantity'))
        return result['total_qty'] or 0