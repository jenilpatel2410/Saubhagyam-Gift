import os
from management_app.models import *
from rest_framework import serializers
from ..serializer.ProductImageSerializer import MobileProductImageSerializer

class FavouriteSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    deleted_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)  

    class Meta:
        model = FavouriteModel
        fields = ('id', 'user_id', 'product_id', 'status', 'created_at', 'updated_at', 'deleted_at')


class ProductSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source='name')
    distributor_price = serializers.DecimalField(source='distributer_price', max_digits=10, decimal_places=2)
    brand_id = serializers.IntegerField(source='brand.id', read_only=True)
    super_distributor_rate = serializers.DecimalField(source='super_distributer_price', max_digits=10, decimal_places=2)
    gst_percentage = serializers.FloatField(source='gst')
    end_use_sales_discount = serializers.FloatField(source='sales_discount')
    limited_stock_status = serializers.CharField(source='limited_stock')
    out_of_stock_status = serializers.CharField(source='out_of_stock')
    category_id_old = serializers.SerializerMethodField()
    sub_category_id_old = serializers.SerializerMethodField(read_only=True)

    favourite = serializers.SerializerMethodField()
    product_images = MobileProductImageSerializer(many=True, read_only=True, source='images')

    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    deleted_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  

    class Meta:
        model = ProductModel
        fields = ('id', 'category_id_old','sub_category_id_old', 'product_name', 'distributor_price', 'retailer_price', 'product_price', 'description', 'brand_id', 'is_favourite', 'item_code', 
                'group', 'model', 'color', 'company_code', 'unit', 'hsn_code', 'upc_barcode', 'lan_barcode',
                'super_distributor_rate', 'gst_percentage', 'end_use_sales_discount', 'warranty', 'feature', 'weight',
                'document', 'web_link', 'video_link', 'short_name','limited_stock_status', 'out_of_stock_status', 
                'created_at',  'updated_at', 'deleted_at', 'favourite', 'product_images')


    def get_favourite(self, obj):
        user_id = self.context.get('request').data.get('user_id')
        fav = obj.favouritemodel_set.filter(user_id=user_id)
        return FavouriteSerializer(fav, many=True).data
    
    def get_category_id_old(self,obj):
        first_category = obj.category.values_list('id', flat=True).first()
        return first_category
    
    def get_sub_category_id_old(self, obj):
        first_category = obj.sub_category.values_list('id', flat=True).first()
        return first_category
