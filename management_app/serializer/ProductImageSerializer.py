from rest_framework import serializers
from ..models import ProductImageModel
import os

class MobileProductImageSerializer(serializers.ModelSerializer):
    product_id = serializers.SerializerMethodField()
    product_image = serializers.ImageField(source="image")
    is_primary = serializers.SerializerMethodField() 
    
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
 
    class Meta:
        model = ProductImageModel
        fields = ['id', 
                  'product_id',
                  'product_image',
                  'created_at',
                  'updated_at',
                  'deleted_at',
                  'is_primary']

    def get_product_id(self, obj):
        return str(obj.product.id)

  
    def get_is_primary(self, obj): 
        if obj.is_primary:
            return 1
        else:
            return 0
