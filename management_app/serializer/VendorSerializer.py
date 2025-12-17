from rest_framework import serializers
from ..models import *
from user_app.serializers import *


class VendorListSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField(read_only=True)
    last_name = serializers.SerializerMethodField(read_only=True)
    many_address = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(source='user.email',default='')

    def get_many_address(self,obj):
        if obj.many_address.exists():
            address = []
            for addr in obj.many_address.all():
               address.append(AddressSerializerForCreate(addr).data)
            return address
        return []
    
    def get_first_name(self, obj):
        if obj.name:
            parts = obj.name.strip().split(" ", 1)
            return parts[0] if parts else ""
        return ""

    def get_last_name(self, obj):
        if obj.name:
            parts = obj.name.strip().split(" ", 1)
            return parts[1] if len(parts) > 1 else ""
        return ""

    class Meta:
        model = ContactModel
        fields = ['id','name','first_name','last_name','user','phone_no','contact_role','many_address','contact_type','email','gstin','pan_number']

class VendorSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    # many_address = AddressSerializerForCreate(many=True,required=False)
    many_address = serializers.ListField(write_only=True,required=False)
    get_first_name = serializers.SerializerMethodField(read_only=True)
    get_last_name = serializers.SerializerMethodField(read_only=True)

    def get_get_first_name(self, obj):
        if obj.name:
            return obj.name.split(" ", 1)[0]
        return ""

    def get_get_last_name(self, obj):
        if obj.name and " " in obj.name:
            return obj.name.split(" ", 1)[1]
        return ""

    def create(self, validated_data):
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        address_data = validated_data.pop('many_address','')


        user = UserModel.objects.filter(email = email).first()
        if not user:
            user = UserModel.objects.create(email=email,first_name=first_name,last_name=last_name)
            
        profile = ProfileModel.objects.filter(user = user).first()
        if not profile:
            profile = ProfileModel.objects.create(user = user)

        validated_data['user'] = user
        validated_data['name'] = f'{user.first_name} {user.last_name}'

        validated_data['email'] = user.email
        
        instance = super().create(validated_data)

        if address_data:
            for addr in address_data:
               address = AddressModel.objects.create(**addr,full_name=f"{first_name} {last_name}",mobile=user.mobile_no)
               instance.many_address.add(address)
               instance.save()
        
        instance.refresh_from_db()

        return instance
    
    def update(self,instance,validated_data):
        user = instance.user
        user_first_name = validated_data.pop('first_name', None)
        user_last_name = validated_data.pop('last_name', None)
        user_email = validated_data.pop('email', None)
        address_data = validated_data.pop('many_address', None)

        if user_first_name:
            user.first_name = user_first_name
        if user_last_name:
            user.last_name = user_last_name
        if user_email:
            user.email = user_email
        user.save()

        if instance.name != f'{user.first_name} {user.last_name}':
            instance.name = f'{user.first_name} {user.last_name}'

        if address_data:
            for addr in address_data:
                addr_id = addr.get('id','')
                if addr_id:
                    try:
                        address=instance.many_address.get(id=addr_id)
                        for key, value in addr.items():
                            if key != "id":  # skip the id field
                              setattr(address, key, value)
                        address.save()
                    except AddressModel.DoesNotExist:
                        raise serializers.ValidationError({"address": f"Address with id {addr_id} not found"})
                # else:
                #     address = AddressModel.objects.create(**addr,full_name=f'{user.first_name} {user.last_name}',mobile=instance.phone_no)
                #     instance.many_address.add(address)

        instance = super().update(instance,validated_data)
        instance.refresh_from_db()
        return instance



    class Meta:
        model = ContactModel
        fields = ['id','user','first_name','last_name','get_first_name','get_last_name','email','many_address','contact_role','phone_no','contact_type', 'gstin', 'pan_number']