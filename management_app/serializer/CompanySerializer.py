from rest_framework import serializers
from user_app.serializers import *
from ..models import *



class CompanySerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True,required=False)
    address = AddressSerializerForCreate(required=False)
    address_details = serializers.SerializerMethodField(read_only=True)

    def get_address_details(self,obj):
        if obj.address:
            return AddressSerializerForCreate(obj.address).data
        return {}

    def create(self, validated_data):
        address_data = validated_data.pop('address','')
        instance  = super().create(validated_data)

        if address_data:
            address = AddressModel.objects.create(**address_data,full_name=instance.name,mobile=instance.phone_no)
            instance.address = address
            instance.save()
        
        instance.refresh_from_db()

        return instance
   
    def update(self,instance,validated_data):
        address_data = validated_data.pop('address','')
        
        super().update(instance,validated_data)

        if address_data:
            if instance.address:
               address = instance.address
               for field, value in address_data.items():
                  setattr(address, field, value)
               address.save()
            address = AddressModel.objects.create(**address_data,full_name=instance.name,mobile=instance.phone_no)
            instance.address = address 
            instance.save() 

        return instance
            
    class Meta:
        model = CompanyModel
        fields = ['id','name','logo','code','email','phone_no','gstin','pan_number','address','is_active','address_details']

class CompanyListSerializer(serializers.ModelSerializer):
    address = AddressSerializerForCreate(read_only=True)

    class Meta:
        model = CompanyModel
        fields = ['id','name','code','email','phone_no','address','pan_number','gstin']