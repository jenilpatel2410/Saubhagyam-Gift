from rest_framework import serializers
from ..models import *
from user_app.serializers import *


class VendorListSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField(read_only=True)
    last_name = serializers.SerializerMethodField(read_only=True)
    many_address = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField()  #source='email', default=''

    def get_many_address(self, obj):
        if obj.many_address.exists():
            return AddressSerializerForCreate(
                obj.many_address.all(),
                many=True
            ).data
        return []

    def get_first_name(self, obj):
        if obj.name:
            return obj.name.split(" ", 1)[0]
        return ""

    def get_last_name(self, obj):
        if obj.name and " " in obj.name:
            return obj.name.split(" ", 1)[1]
        return ""

    class Meta:
        model = ContactModel
        fields = [
            'id',
            'name',
            'first_name',
            'last_name',
            'user',
            'phone_no',
            'contact_role',
            'many_address',
            'contact_type',
            'email',
            'gstin',
            'pan_number'
        ]


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
        request = self.context.get('request')

        # ---- Extract contact-level info ----
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        email = validated_data.pop('email')
        address_data = validated_data.pop('many_address', [])

        # ---- Link or create UserModel for identity ----
        user = UserModel.objects.filter(email=email).first()
        if not user:
            user = UserModel.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name
            )
        
        # Ensure Profile exists
        ProfileModel.objects.get_or_create(user=user)

        # ---- Prepare contact-level fields ----
        validated_data['user'] = user
        validated_data['admin_user'] = request.user
        validated_data['name'] = f'{first_name} {last_name}'
        validated_data['email'] = email  # contact-level email

        # ---- Create Contact ----
        contact = super().create(validated_data)

        # ---- Add addresses if any ----
        for addr in address_data:
            address = AddressModel.objects.create(
                **addr,
                full_name=f'{first_name} {last_name}',
                mobile=user.mobile_no
            )
            contact.many_address.add(address)

        contact.refresh_from_db()
        return contact
    
    def update(self, instance, validated_data):
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        email = validated_data.pop('email', None)
        address_data = validated_data.pop('many_address', None)

        # ---- CONTACT-LEVEL UPDATES ----
        if first_name or last_name:
            fname = first_name or instance.name.split(" ", 1)[0]
            lname = last_name or (
                instance.name.split(" ", 1)[1]
                if " " in instance.name else ""
            )
            instance.name = f"{fname} {lname}".strip()

        if email:
            instance.email = email

        # ---- ADDRESS HANDLING (SAFE) ----
        if address_data:
            for addr in address_data:
                addr_id = addr.get('id')
                if addr_id:
                    try:
                        address = instance.many_address.get(id=addr_id)
                        for key, value in addr.items():
                            if key != "id":
                                setattr(address, key, value)
                        address.save()
                    except AddressModel.DoesNotExist:
                        raise serializers.ValidationError(
                            {"address": f"Address with id {addr_id} not found"}
                        )

        instance = super().update(instance, validated_data)
        instance.refresh_from_db()
        return instance



    class Meta:
        model = ContactModel
        fields = ['id','user','first_name','last_name','get_first_name','get_last_name','email','many_address','contact_role','phone_no','contact_type', 'gstin', 'pan_number']