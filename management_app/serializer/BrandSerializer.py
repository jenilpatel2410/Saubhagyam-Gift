from rest_framework import serializers
from ..models import *


class MobileBrandSerializer(serializers.ModelSerializer):
    brand_name=serializers.CharField(source="name")
    brand_image=serializers.ImageField(source="image")
    description=serializers.CharField()
    brand_display_number=serializers.IntegerField(source="number")

    class Meta:
        model = BrandModel
        fields = (
            'id',
            'brand_name',
            'brand_image',
            'description',
            'brand_display_number', 
        )

class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = BrandModel
        fields = ['id','name','number','description']
    
   

    