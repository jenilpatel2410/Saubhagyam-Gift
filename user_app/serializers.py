from rest_framework import serializers
from .models import *
from management_app.models import *
from django.contrib.auth.models import Group
from phonenumber_field.phonenumber import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from phonenumber_field.phonenumber import to_python
from django.db import transaction, IntegrityError

class ProfileSerializer(serializers.ModelSerializer):
    contact = serializers.CharField(source="mobile_no")
    class Meta:
        model = ProfileModel
        fields = [
            "id", "contact","profile_pic", "addresses", "otp", "otp_requested_at","os_type",
        ]

class AddressSerializer(serializers.ModelSerializer):
    contact = serializers.CharField(source='mobile')
    
    class Meta:
        model = AddressModel
        fields = ["id","full_name","street","city","state","pincode","contact","address"]

    def update(self, instance, validated_data):
        mobile = validated_data.pop('mobile', '')
        if mobile:
            instance.mobile = mobile
            instance.save()       
        return super().update(instance, validated_data)
    
class AddressSerializerForCreate(serializers.ModelSerializer):

    class Meta:
        model = AddressModel
        fields = ['id','full_name','city','state','country','pincode','address']

class AdminSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        request_user = self.context.get('request').user
        
        if request_user.role and request_user.role.type == 'Admin':
            super().create(validated_data)

       
        raise serializers.ValidationError("You do not have permission to update this user.")
    
    def update(self, instance, validated_data):
        request_user = self.context.get('request').user

        if request_user.role and request_user.role.type == 'Admin':
        
            return super().update(instance, validated_data)
        
        raise serializers.ValidationError("You do not have permission to update this user.")
    
    class Meta:
        model = UserModel
        fields = ['id','first_name','last_name','email','mobile_no','role','is_active']

class UserSerializer(serializers.ModelSerializer):
    address =  serializers.ListField(required=False,write_only=True)
    address_details = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    transport = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()

    def get_address_details(self,obj):
        if obj.address.exists():
            address = []
            for addr in obj.address.all():
               address.append(AddressSerializerForCreate(addr).data)
            return address
        return {}
    
    def validate_mobile_no(self, value):
        if not value:
            raise serializers.ValidationError("Mobile number is required.")
        user_id = self.instance.id if self.instance else None

        # # Check if another user already has this mobile number
        # if UserModel.objects.filter(mobile_no=value).exclude(id=user_id).exists():
        #     raise serializers.ValidationError("Mobile number already exists.")
        return value


    def create(self, validated_data):
        address_data = validated_data.pop("address", None)
        password = validated_data.pop("password", None)
        transport = validated_data.pop("transport", None)
        admin_user = self.context.get("admin_user")

        email = validated_data.get("email")

        with transaction.atomic():
            #  Reuse user if email already exists
            user, created = UserModel.objects.get_or_create(
                email=email,
                defaults=validated_data
            )

            #  Set password only if user is newly created
            if created and password:
                user.set_password(password)
                user.save()

            #   Address handling (only when user is created)
            if created and address_data:
                for addr in address_data:
                    address = AddressModel.objects.create(
                        **addr,
                        full_name=f"{user.first_name} {user.last_name}",
                        mobile=user.mobile_no
                    )
                    user.address.add(address)

            #  Create contact for this admin (tenant)
            ContactModel.objects.get_or_create(
                user=user,
                admin_user=admin_user,
                defaults={
                    "name": f"{user.first_name} {user.last_name}",
                    "phone_no": user.mobile_no,
                    "email": user.email,
                    "transport": transport,
                }
            )

            #  Profile is global, create once
            ProfileModel.objects.get_or_create(
                user=user,
                defaults={"mobile_no": user.mobile_no}
            )

            return user
    
    
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address',None)
        password = validated_data.get("password", None)
        transport = validated_data.pop("transport", None)
        
        admin_user = self.context.get("admin_user")  


        instance = super().update(instance,validated_data)
        if password:
                instance.set_password(password)
                instance.save()

        if address_data:
            for addr in address_data:
                addr_id = addr.get('id','')
                if addr_id:
                    try:
                        address=instance.address.get(id=addr_id)
                        for key, value in addr.items():
                            if key != "id":  # skip the id field
                                setattr(address, key, value)
                        address.full_name =f'{instance.first_name} {instance.last_name}'
                        address.mobile=instance.mobile_no
                        address.save()
                    except AddressModel.DoesNotExist:
                        raise serializers.ValidationError({"address": f"Address with id {addr_id} not found"})
                else:
                    address = AddressModel.objects.create(**addr,mobile=instance.mobile_no)
                    instance.address.add(address)    
                

        contact, _ = ContactModel.objects.get_or_create(user=instance,admin_user=admin_user)
        # contact.admin_user = admin_user       

        contact.name = f"{instance.first_name} {instance.last_name}"
        contact.phone_no = instance.mobile_no
        contact.email = instance.email
        contact.transport = transport if transport is not None else contact.transport
        contact.save()
        if instance.address.exists():
            contact.many_address.set(instance.address.all())

        profile, _ = ProfileModel.objects.get_or_create(user=instance)
        profile.mobile_no = instance.mobile_no
        profile.save()
        if instance.address.exists():
            profile.addresses.set(instance.address.all())


        
        
        instance.refresh_from_db()

        return instance
              
    class Meta:
        model = UserModel
        fields = ['id','first_name','last_name','password','email','mobile_no','role','address','address_details','firm_name','transport']


class ContactUpdateSerializer(serializers.ModelSerializer):
    address = serializers.ListField(required=False)
    
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        role_id = self.initial_data.get('role')

        # ---------- SAFE FIELD MAPPING ----------
        # frontend -> ContactModel
        if 'first_name' in self.initial_data or 'last_name' in self.initial_data:
            first = self.initial_data.get('first_name', '').strip()
            last = self.initial_data.get('last_name', '').strip()
            instance.name = f"{first} {last}".strip()

        if 'mobile_no' in self.initial_data:
            instance.phone_no = self.initial_data.get('mobile_no')

        if 'email' in validated_data:
            instance.email = validated_data.get('email')

        if 'transport' in validated_data:
            instance.transport = validated_data.get('transport')

        instance.save()
        
        if role_id:
            try:
                instance.user.role_id = role_id
                instance.user.save(update_fields=['role'])
            except Exception:
                raise serializers.ValidationError(
                    {"role": "Invalid role"}
                )

        # ---------- ADDRESS HANDLING ----------
        if not address_data:
            return instance

        for addr in address_data:
            addr_id = addr.get('id')

            if addr_id:
                try:
                    address = instance.many_address.get(id=addr_id)
                    for key, value in addr.items():
                        if key != 'id':
                            setattr(address, key, value)
                    address.save()
                except AddressModel.DoesNotExist:
                    raise serializers.ValidationError(
                        {"address": f"Address with id {addr_id} not found"}
                    )
            else:
                address = AddressModel.objects.create(**addr)
                instance.many_address.add(address)

        return instance



    class Meta:
        model = ContactModel
        fields = [
            'name',
            'phone_no',
            'email',
            'transport',
            'address',   # list of address dicts (same as UserSerializer)
        ]


class UserListSerializer(serializers.ModelSerializer):
    many_address = serializers.SerializerMethodField()

    # 👇 show from Contact first, fallback to User
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    firm_name = serializers.SerializerMethodField()

    role = serializers.CharField(source='user.role.type', default="")
    role_id = serializers.IntegerField(source='user.role.id', read_only=True)

    def get_first_name(self, obj):
        if obj.name:
            return obj.name.split(' ')[0]
        return obj.user.first_name if obj.user else ""

    def get_last_name(self, obj):
        if obj.name and len(obj.name.split(' ')) > 1:
            return " ".join(obj.name.split(' ')[1:])
        return obj.user.last_name if obj.user else ""

    def get_firm_name(self, obj):
        # firm_name is business-specific → keep it on Contact
        return obj.name or (obj.user.firm_name if obj.user else "")

    def get_many_address(self, obj):
        if obj.many_address.exists():
            return AddressSerializerForCreate(
                obj.many_address.all(),
                many=True
            ).data
        return []

    class Meta:
        model = ContactModel
        fields = [
            'id',
            'name',
            'first_name',
            'last_name',
            'email',
            'role',
            'role_id',
            'phone_no',
            'many_address',
            'firm_name',
            'transport',
        ]


class MobileUserSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)
    contact = serializers.CharField(source="mobile_no")
    firebase_token = serializers.CharField(source="token")

    profile_image = serializers.ImageField(source="profilemodel.profile_pic",required=False, allow_null=True)
    otp = serializers.CharField(source="profilemodel.otp", read_only=True)
    os_type = serializers.CharField(source="profilemodel.os_type", read_only=True)

    address = serializers.CharField(source="address.first.address", read_only=True)
    pincode = serializers.CharField(source="address.first.pincode", read_only=True)
    
    role_type = serializers.SerializerMethodField()

    def get_role_type(self, obj):
        return obj.role.type if obj.role else ''
    # addresses = AddressSerializer(many=True)
    class Meta:
        model = UserModel
        fields = ["id","first_name", "last_name","email","role", "role_type","contact","address","pincode","profile_image","otp","os_type", "is_active","created_at","firebase_token"]

    def create(self, validated_data):
        validated_data["is_active"] = True
        
        if "role" not in validated_data or not validated_data["role"]:
            try:
                retailer_role = RoleModel.objects.get(type__iexact="Retailer")
                validated_data["role"] = retailer_role
            except RoleModel.DoesNotExist:
                validated_data["role"] = None

        return super().create(validated_data)
    
    def update(self, instance, validated_data):

        profile_data = validated_data.pop("profilemodel", {})

        instance = super().update(instance, validated_data)

        profile = getattr(instance, "profilemodel", None)
        if profile and "profile_pic" in profile_data:
            profile.profile_pic = profile_data["profile_pic"]
            profile.save()

        return instance
    
class CountriesSerializer(serializers.ModelSerializer):

    all_state = serializers.SerializerMethodField(read_only=True)

    def get_all_state(self, obj):
        get_all_country = StatesModel.objects.filter(country=obj).values()
        return get_all_country

    class Meta:
        model = CountryModel
        fields = ['id','country_name','country_code','currency','calling_code', 'all_state']


class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.SerializerMethodField(read_only=True)
    all_cities = serializers.SerializerMethodField(read_only=True)

    def get_all_cities(self, obj):
        get_all_cities = CitiesModel.objects.filter(state=obj).values()
        return get_all_cities

    def get_country_name(self, obj):
        return obj.country.country_name

    class Meta:
        model = StatesModel
        fields = ['id','country','country_name','name','all_cities']


class CitiesSerializer(serializers.ModelSerializer):
    state_name = serializers.SerializerMethodField(read_only=True)
    country_name = serializers.SerializerMethodField(read_only=True)

    def get_state_name(self, obj):
        return obj.state.name

    def get_country_name(self, obj):
        return obj.country.country_name


    class Meta:
        model = CitiesModel
        fields = ['id','country','country_name','state','state_name','name']

class WebProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email',required=False)
    first_name = serializers.CharField(source='user.first_name',required=False)
    last_name =  serializers.CharField(source='user.last_name',required=False)
    addresses = serializers.SerializerMethodField(read_only=True)
        
    def get_addresses(self, obj):
        return AddressSerializer(obj.addresses.all(), many=True).data

    def update(self,instance,validated_data):
        user_data = validated_data.pop('user',{})
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        
        return super().update(instance, validated_data)

    class Meta:
        model = ProfileModel
        exclude = ['user']
        
class WebAddressSerializer(serializers.ModelSerializer):
    country_obj = serializers.SerializerMethodField(read_only=True)
    state_obj = serializers.SerializerMethodField(read_only=True)
    city_obj = serializers.SerializerMethodField(read_only=True)
    country_calling_code = serializers.SerializerMethodField(read_only=True)
    country_code = serializers.SerializerMethodField(read_only=True)
    mobile_without_ext = serializers.SerializerMethodField(read_only=True)
    another_mobile_without_ext = serializers.SerializerMethodField(read_only=True)
    # not_in_gujarat = serializers.SerializerMethodField(read_only=True)

    def get_country_obj(self, obj):
        return {'id': obj.fcountry.id, 'name': obj.fcountry.country_name} if obj.fcountry_id else None

    def get_state_obj(self, obj):
        return {'id': obj.fstate.id, 'name': obj.fstate.name} if  obj.fstate_id else None

    def get_city_obj(self, obj):
        return {'id': obj.fcity.id, 'name': obj.fcity.name} if obj.fcity_id else None

    def get_country_calling_code(self, obj):
        return obj.fcountry.calling_code if obj.fcountry_id else None
    
    def get_country_code(self, obj):
        if not obj.mobile:
            return None
        try:
            phone_obj = phonenumbers.parse(str(obj.mobile), None)
            if phonenumbers.is_valid_number(phone_obj):
                return phone_obj.country_code
        except NumberParseException:
            pass
        return obj.fcountry.calling_code if obj.fcountry_id else None

    def get_mobile_without_ext(self, obj):
        if not obj.mobile:
            return None
        try:
            phone_details = phonenumbers.parse(str(obj.mobile), None)  # ✅ no fixed country
            if phonenumbers.is_valid_number(phone_details):  # extra validation
                return phone_details.national_number
            return obj.mobile
        except NumberParseException:
            return obj.mobile  

    def get_another_mobile_without_ext(self, obj):
        if not obj.another_mobile:
            return None
        try:
            phone_details = phonenumbers.parse(str(obj.another_mobile), None)  # ✅ no fixed country
            if phonenumbers.is_valid_number(phone_details):  # extra validation
                return phone_details.national_number
            return obj.another_mobile
        except NumberParseException:
            return obj.another_mobile 
    
    # def get_not_in_gujarat(self, obj):
    #     return obj.state and obj.state.name != "GUJARAT" if obj.state else False
    
    class Meta:
        model = AddressModel
        fields = '__all__'
        
    def create(self, validated_data):
        fcity = validated_data.get('fcity')
        fstate = validated_data.get('fstate')
        fcountry = validated_data.get('fcountry')

        if fcountry:
            validated_data['country'] = fcountry.country_name
        if fstate:
            validated_data['state'] = fstate.name
        if fcity:
            validated_data['city'] = fcity.name

        return super().create(validated_data)

    def update(self, instance, validated_data):
        fcity = validated_data.get('fcity')
        fstate = validated_data.get('fstate')
        fcountry = validated_data.get('fcountry')

        # Update names if FK provided
        if fcountry:
            instance.country = fcountry.country_name
        if fstate:
            instance.state = fstate.name
        if fcity:
            instance.city = fcity.name
        mobile = validated_data.pop('mobile', '')
        if mobile:
            instance.mobile = mobile
            instance.save()       
        return super().update(instance, validated_data)
    
class WebUserSerializer(serializers.ModelSerializer):
    address =  AddressSerializerForCreate(required=False,write_only=True)
    address_details = serializers.SerializerMethodField(read_only=True)
    profile_image = serializers.ImageField(source="profilemodel.profile_pic",required=False, allow_null=True)
    otp = serializers.CharField(source="profilemodel.otp", read_only=True)
    otp_requested_at = serializers.DateTimeField(source="profilemodel.otp_requested_at",format="%Y-%m-%d %H:%M:%S", read_only=True)
    os_type = serializers.CharField(source="profilemodel.os_type", read_only=True)
    phone_no = serializers.CharField(source="mobile_no", read_only=True)
    group = serializers.SerializerMethodField()
    cart_counter = serializers.SerializerMethodField()
    
    def get_address_details(self,obj):
        if obj.address.exists():
            address = []
            for addr in obj.address.all():
               address.append(AddressSerializerForCreate(addr).data)
            return address
        return {}
    
    def get_group(self, obj):
        group = obj.groups.first()
        return group.name if group else ""

    def get_cart_counter(self, obj):
        from management_app.models import Cart  
        return Cart.objects.filter(user=obj).count()
    
    def create(self, validated_data):
        validated_data["is_active"] = True
        
        if "role" not in validated_data or not validated_data["role"]:
            try:
                retailer_role = RoleModel.objects.get(type__iexact="Retailer")
                validated_data["role"] = retailer_role
            except RoleModel.DoesNotExist:
                validated_data["role"] = None

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address',None)

        super().update(instance,validated_data)

        if address_data:
            if instance.address.exists():
               address = instance.address.first()
               for field, value in address_data.items():
                  setattr(address, field, value)
               address.save()
            else:
               address = AddressModel.objects.create(**address_data,mobile=instance.mobile_no)
               instance.address.add(address)
               instance.save()
        
        instance.refresh_from_db()

        return instance
              
    class Meta:
        model = UserModel
        fields = ['id','first_name','last_name','email','mobile_no','phone_no','profile_image','otp','otp_requested_at','os_type','role','address','address_details','firm_name','is_staff','is_superuser','group', 'cart_counter']


class ContactUsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactUsModel
        fields = '__all__'