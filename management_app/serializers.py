from rest_framework import serializers
from .models import *
from user_app.models import *
import slugify,json



class RoleSerilaizer(serializers.ModelSerializer):

    class Meta:
        model = RoleModel
        fields = ['id','name','type']

class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = CountryModel
        fields =  ['id','country_name','calling_code','country_code']


class SerialNoSerializer(serializers.ModelSerializer):
    # product_name = serializers.CharField(source='product.name',default='')

    class Meta:
        model = SerialNumbersModel
        fields = ['id','serial_no','product']

class InquirySerializer(serializers.ModelSerializer):
    person = serializers.SerializerMethodField()
    product = serializers.CharField(source='product.name',read_only=True,default="")

    def get_person(self, obj):
        if obj.name:
            return f"{obj.name.first_name} {obj.name.last_name}"
        return None

    class Meta:
        model = InquiryModel
        fields = ['id','person','product','quantity','description','status']

class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = FeedbackModel
        fields = ['id','name','email','title','description']


class RetailerSerializer(serializers.ModelSerializer):
    firm_name = serializers.SerializerMethodField()
    firm = serializers.CharField(write_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    def get_firm_name(self,obj):
        try:
            firm_name=FirmModel.objects.get(user=obj)
            return firm_name.name
        except FirmModel.DoesNotExist:
            return ''
        
    def update(self, instance, validated_data):
        firm = validated_data.pop('firm','')
        if firm:
            try:
                firm_instance=FirmModel.objects.get(user=instance)
                firm_instance.name=firm
                firm_instance.save()
            except FirmModel.DoesNotExist:
                FirmModel.objects.create(name=firm,user=instance)
        return super().update(instance, validated_data)
    
    class Meta:
        model = UserModel
        fields = ['id','first_name','last_name','role','mobile_no','address','firm_name','firm','']
        
class BlogModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogModel
        fields = ["id", "title", "banner", "content", "is_published", "published_at"]
        read_only_fields = fields

class ClientSerializer(serializers.ModelSerializer):
    
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    class Meta:
        model = Client
        fields = ["id","name","description","image"]
        
    def get_name(self, obj):
        lang = self.context.get("lang", "en")
        translation = obj.translations.filter(language_code=lang).first()
        return translation.name if translation and translation.name else obj.name

    def get_description(self, obj):
        lang = self.context.get("lang", "en")
        translation = obj.translations.filter(language_code=lang).first()
        return translation.description if translation and translation.description else obj.description