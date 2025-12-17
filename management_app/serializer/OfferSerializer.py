from rest_framework import serializers
from ..models import *

class OfferSerializer(serializers.ModelSerializer):    
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)
    valid_from = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    valid_to = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    role_name = serializers.CharField(source='roles.type', read_only=True)
    discount_type_display = serializers.SerializerMethodField()

    def get_discount_type_display(self,obj):
        if obj.discount_type:
            if obj.discount_type == 'flat':
                return f' ₹ {obj.discount_value}'
            elif obj.discount_type == 'percentage':
                return f'{obj.discount_value} %'

    class Meta:
        model = OfferModel
        fields = ['id','title','image','roles','role_name','coupon_code','discount_type','discount_type_display','discount_value','valid_from','valid_to','created_at']

        
class MobileOfferSliderSerializer(serializers.ModelSerializer):    
    offer_slider_image=serializers.ImageField(source="image")
    slider_number = serializers.IntegerField(source="banner_number")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    role_name = serializers.CharField(source='roles.name',default='')
 
    class Meta:
        model = OfferSliderModel
        fields =(
            'id',
            'offer_slider_image',
            'slider_number',
            'role_name',
            'created_at',
            'updated_at',
            'deleted_at',
        )

class OnlinePaymentOfferSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)
    
    class Meta:
        model = OnlinePaymentOfferModel
        fields = ['id','start_price','end_price','percentage_off','created_at']

class MobileOnlinePaymentOfferSerializer(serializers.ModelSerializer):
    start_price_value = serializers.CharField(source='start_price')
    end_price_value = serializers.CharField(source = 'end_price')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)
    
    class Meta:
        model = OnlinePaymentOfferModel
        fields = ['id','start_price_value','end_price_value','percentage_off','created_at']

class OfferSliderSerializer(serializers.ModelSerializer):
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)
    
    def create(self, validated_data):
        # Remove serializer-only field so it doesn't go to model.create()
        validated_data.pop('remove_image', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image = validated_data.pop('remove_image',False)
        if image and instance.image:
                instance.image.delete(save=False)
                instance.image = None
        return super().update(instance,validated_data)

    class Meta:
        model = OfferSliderModel
        fields = ['id','image','banner_number','remove_image']
