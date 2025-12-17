from rest_framework import serializers
from ..models import *
from management_app.serializer.ProductSerializer import MobileProductSerializer,ProductImageSerializer
from django.utils.text import slugify

class CartSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = [
            "id", "user_id", "product_id", "brand_id",
            "qty", "price","discount","discount_price","status",
            "total_price", "created_at", "updated_at","product"
        ]
        read_only_fields = ["price", "created_at", "updated_at", "total_price"]
        
    def get_product(self, obj):
        lang = self.context.get('lang', 'en')
        request = self.context.get('request')
        return MobileProductSerializer(
            obj.product,
            context={'lang': lang, 'request': request}
        ).data
        
        
class WebCartSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    selling_price = serializers.IntegerField(
        source='product.base_price', read_only=True)
    product_image = serializers.SerializerMethodField('get_product_image')
    product_price = serializers.SerializerMethodField(read_only=True)
    encrypted_id = serializers.SerializerMethodField(read_only=True)
    category_slug = serializers.SerializerMethodField(read_only=True)
    sub_category_slug = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.SerializerMethodField(read_only=True)
    total = serializers.CharField(source="total_price", read_only=True)

    def get_product_image(self, obj):
        # photo_url = obj.product.image1.url
        # return photo_url
    
        request = self.context.get('request')
        first_image = ProductImageModel.objects.filter(product=obj.product).order_by('id').first()
        if first_image and first_image.image:
            url = first_image.image.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_category_slug(self,obj):
        return 'festival-celebration' 
        
    def get_sub_category_slug(self,obj):
        return 'rakshabandhan'

    def get_product_price(self, obj):
        """
        Return product price depending on request.user.role.type
        """
        request = self.context.get("request")
        if request and hasattr(request, "user") and hasattr(request.user, "role"):
            role_type = getattr(request.user.role, "type", None)

            if role_type == "Retailer" and obj.product.retailer_price:
                return obj.product.retailer_price
            elif role_type == "Wholesaler" and obj.product.distributer_price:
                return obj.product.distributer_price
            elif role_type == "Distributer" and obj.product.distributer_price:
                return obj.product.distributer_price
        
        # Default: MRP
        return obj.product.retailer_price

    # def to_representation(self, instance):
    #     rep = super(CartSerializer, self).to_representation(instance)
    #     rep['product'] = instance.product.name
    #     if instance.user is not None:
    #         rep['email'] = instance.user.email
    #     else:
    #         rep['visitor'] = instance.visitor.visitor_id if instance.visitor else ''
    #     return rep
    
    def get_encrypted_id(self, obj):
        if obj.product:
            return obj.product.encrypted_id
        return None
    
    # def get_product_name(self,obj):
    #     if obj.product:
    #         return obj.product.name
    #     return None
    
    def get_product_name(self, obj):
        lang = self.context.get('lang', 'en')
        product = obj.product

        if lang == 'en':
            return product.name
        
        translation = ProductTranslation.objects.filter(product=product, language_code=lang).first()
        if translation and translation.name:
            return translation.name

        return product.name
    class Meta:
        model = Cart
        fields = "__all__"
        