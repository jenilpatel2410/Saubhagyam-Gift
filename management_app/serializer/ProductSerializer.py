from rest_framework import serializers
from ..models import *
import slugify,json
from management_app.serializer.ProductImageSerializer import MobileProductImageSerializer
from management_app.serializer.FavouriteSerializer import FavouriteSerializer


class ProductImageSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()

    def get_product_name(self,obj):
        if obj.product:
            return obj.product.name

        return ''

    class Meta:
        model = ProductImageModel
        fields = ['id','product','product_name','image']


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    sub_category = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source='brand.name',read_only=True)
    company_name = serializers.CharField(source='company.name',read_only=True)
    stock = serializers.SerializerMethodField()

    
    def get_category(self, obj):
        return ", ".join([cat.name for cat in obj.category.all()]) if obj.category.exists() else ""

    def get_sub_category(self, obj):
        return ", ".join([sub.name for sub in obj.sub_category.all()]) if obj.sub_category.exists() else ""
    
    def get_images(self,obj):
        return ProductImageSerializer(obj.images.all(),many=True).data
    
    def get_stock(self,obj):
        stock = Inventory.objects.filter(product=obj).first()
        if stock and stock.quantity:
            return stock.quantity
        else:
            return 0
    
    class Meta:
        model = ProductModel
        fields = ['id','name','short_name','category','sub_category','product_price','unit','purchase_price','warehouse_section','home_categories','brand_name','images','item_code','barcode_image','company_name','short_description','description','stock']


class ProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    sub_category = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source='brand.name',read_only=True)
    company_name = serializers.CharField(source='company.name',read_only=True)
    stock = serializers.SerializerMethodField()

    
    def get_category(self, obj):
        return ", ".join([cat.name for cat in obj.category.all()]) if obj.category.exists() else ""

    def get_sub_category(self, obj):
        return ", ".join([sub.name for sub in obj.sub_category.all()]) if obj.sub_category.exists() else ""
    
    def get_images(self,obj):
        return ProductImageSerializer(obj.images.all(),many=True).data

    def get_document(self,obj):
        return obj.document.url if obj.document else None
    
    def get_stock(self,obj):
        stock = Inventory.objects.filter(product=obj).first()
        if stock and stock.quantity:
            return stock.quantity
        else:
            return "No stock information Available"

    class Meta:
        model = ProductModel
        fields = ['id','name','unit','short_name','is_published','category','sub_category','warehouse_section','home_categories','brand_name','item_code','barcode_image','product_price','weight','feature','retailer_price','super_distributer_price','distributer_price','purchase_price','images', 'brand', 'gst', 'warranty','out_of_stock','limited_stock','short_description','description', 'document','company_name','stock']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(write_only=True)
    sub_category = serializers.CharField(write_only=True)
    home_category = serializers.CharField(write_only=True, required=False)
    is_active = serializers.BooleanField(default=True, required=False)
    is_archived = serializers.BooleanField(default=True, required=False)
    is_published = serializers.BooleanField(default=True, required=False)
    #  'category': ['["3","7"]'], 'sub_category': ['["16"]'],  'remove_image_ids': ['33', '35', '36']
    
    def _normalize_ids(self, value):
        """
        Normalize input into a list of integers.
        Handles cases:
        - "1" -> [1]
        - 1 -> [1]
        - ["1", "2"] -> [1, 2]
        - [1, 2] -> [1, 2]
        - "[1,2]" -> [1, 2]
        - "1,2,3" -> [1, 2, 3]
        - ["1,2,3"] -> [1, 2, 3]
        """
        if value is None:
            return []

        # Case: already an int
        if isinstance(value, int):
            return [value]

        # Case: string input
        if isinstance(value, str):
            value = value.strip()

            # Try JSON first (handles "[1,2]" or "1")
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [int(v) for v in parsed]
                return [int(parsed)]
            except Exception:
                pass

            # Handle comma-separated string: "1,2,3"
            if "," in value:
                return [int(v.strip()) for v in value.split(",") if v.strip()]

            # Fallback: single number string
            return [int(value)]

        # Case: list input
        if isinstance(value, list):
            ids = []
            for v in value:
                if isinstance(v, str) and "," in v:
                    ids.extend(int(x.strip()) for x in v.split(",") if x.strip())
                else:
                    ids.append(int(v))
            return ids

        return []

    def create(self, validated_data):
        request = self.context.get('request')
        images = request.FILES.getlist('images')

        categories = self._normalize_ids(validated_data.pop('category', []))
        subcategories = self._normalize_ids(validated_data.pop('sub_category', []))
        home_categories = self._normalize_ids(validated_data.pop('home_category',[]))
        
        if isinstance(categories, str):
            categories = json.loads(categories)   
        elif isinstance(categories,int):
            categories = [categories]

        if isinstance(subcategories, str):
            subcategories = json.loads(subcategories)
        elif isinstance(subcategories,int):
            subcategories = [subcategories]
        

        instance = super().create(validated_data)

        instance.category.set(categories)
        instance.sub_category.set(subcategories)

        if home_categories:
            instance.home_categories.set(home_categories)
        

        if images:
            for image in images:
              ProductImageModel.objects.create(product=instance, image=image)

        return instance
    

    def update(self, instance, validated_data):
        request = self.context.get('request')
        images = request.FILES.getlist('images')
        remove_image_ids = request.data.getlist('remove_image_ids', [])
        remove_document = request.data.get('remove_document','')

        categories = self._normalize_ids(validated_data.pop('category', None))
        subcategories = self._normalize_ids(validated_data.pop('sub_category', None))
        home_categories = self._normalize_ids(validated_data.get('home_category',None))
        remove_images_ids = self._normalize_ids(remove_image_ids)


        instance = super().update(instance,validated_data)

        if categories is not None:
            instance.category.set(categories)
        
        if subcategories is not None:
            instance.sub_category.set(subcategories)

        if remove_document:
            instance.document.delete()

        if home_categories is not None:
            instance.home_categories.set(home_categories)



        if images:
            for image in images:
                ProductImageModel.objects.create(product=instance, image=image)
        
        if remove_images_ids:

            for img_id in remove_images_ids:
               ProductImageModel.objects.filter(id=img_id, product=instance).delete()


        return instance

        
    class Meta:
        model = ProductModel
        fields = '__all__'



class MobileProductSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    feature = serializers.SerializerMethodField()
    short_name = serializers.SerializerMethodField()
    # product_name = serializers.CharField(source = 'name')
    gst_percentage = serializers.IntegerField(source='gst')
    end_use_sales_discount = serializers.IntegerField(source='sales_discount')
    limited_stock_status = serializers.SerializerMethodField()
    out_of_stock_status = serializers.SerializerMethodField()
    super_distributor_rate =serializers.DecimalField(source='super_distributer_price',max_digits=10,   decimal_places=2)
    category_id_old = serializers.SerializerMethodField()
    sub_category_id_old = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    sub_category = serializers.SerializerMethodField()
    product_images = MobileProductImageSerializer(many=True, required = False, source='images')
    # product_images = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    product_order = serializers.SerializerMethodField()
    # description = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    
    def get_product_name(self, obj):
        lang = self.context.get('lang', 'en')
        if lang == 'en':
            return obj.name
        translation = obj.translations.filter(language_code__iexact=lang).first()
        return translation.name if translation and translation.name else obj.name

    def get_short_name(self, obj):
        lang = self.context.get('lang', 'en')
        if lang == 'en':
            return obj.short_name
        translation = obj.translations.filter(language_code__iexact=lang).first()
        return translation.short_name if translation and translation.short_name else obj.short_name

    def get_feature(self, obj):
        lang = self.context.get('lang', 'en')
        if lang == 'en':
            return obj.feature
        translation = obj.translations.filter(language_code__iexact=lang).first()
        return translation.feature if translation and translation.feature else obj.feature

    def get_description(self, obj):
        # original fallback behavior
        if not obj.description or not obj.description.strip():
            return None

        lang = self.context.get('lang', 'en')
        if lang == 'en':
            return obj.description

        translation = obj.translations.filter(language_code__iexact=lang).first()
        return translation.description if translation and translation.description else obj.description
       
    def get_limited_stock_status(self, obj):
        return 1 if str(obj.limited_stock).lower() in ["yes", "true", "1"] else 0

    def get_out_of_stock_status(self, obj):
        return 1 if str(obj.out_of_stock).lower() in ["yes", "true", "1"] else 0
    
    def get_category_id_old(self,obj):
        first_category = obj.category.values_list('id', flat=True).first()
        return first_category
    
    def get_sub_category_id_old(self, obj):
        first_category = obj.sub_category.values_list('id', flat=True).first()
        return first_category
    
    # def get_category(self, obj):
    #     return ", ".join([c.safe_translation_getter('name', language_code=self.context.get('lang', 'en')) for c in obj.category.all()])

    # def get_sub_category(self, obj):
    #     return ", ".join([s.safe_translation_getter('name', language_code=self.context.get('lang', 'en')) for s in obj.sub_category.all()])

    
    def get_category(self, obj):
        return ", ".join([cat.name for cat in obj.category.all()]) if obj.category.exists() else ""

    def get_sub_category(self, obj):
        return ", ".join([sub.name for sub in obj.sub_category.all()]) if obj.sub_category.exists() else ""
    
    # def get_product_images(self, obj):
    #     image = obj.images.filter(is_primary=1).first() or obj.images.first()
    #     if image:
    #         return ProductImageSerializer(image).data
    #     return None
    
    def get_product_order(self, obj):
        from ..serializer.OrderSerializer import MobileOrderLineSerializer
        orders = OrderLinesModel.objects.filter(product=obj)
        return MobileOrderLineSerializer(orders, many=True).data
    
    # def get_description(self, obj):
    #     return obj.description.strip() if obj.description else None
    
    def get_is_favourite(self, obj):
        request = self.context.get("request")
        user_id = None
        if request:
            user_id = request.data.get("user_id") if hasattr(request, "data") else None

            # If user_id is invalid/null → fallback to token user
            if not user_id or str(user_id).lower() in ["", "null", "none"]:
                if hasattr(request, "user") and request.user.is_authenticated:
                    user_id = request.user.id
                else:
                    return 'false'
        
        return 'true' if obj.favouritemodel_set.filter(user_id=user_id).exists() else 'false'

    def get_stock(self,obj):
        inventory = Inventory.objects.filter(product = obj).first()
        if inventory:
            return inventory.quantity
        else:
            return 0
    class Meta:
        model = ProductModel
        fields = ['id','category_id_old','sub_category_id_old','product_name','stock','distributer_price','retailer_price','product_price','description','brand_id','is_favourite','item_code','group','model','color','company_code','unit','hsn_code','upc_barcode',
                  'lan_barcode','barcode_image','super_distributor_rate','gst_percentage','end_use_sales_discount','warranty','feature','weight','document','web_link','video_link','short_name','limited_stock_status','out_of_stock_status','created_at','updated_at',
                  'category','sub_category','product_images','product_order']


class MobileDashboardProductSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    feature = serializers.SerializerMethodField()
    short_name = serializers.SerializerMethodField()
    gst_percentage = serializers.IntegerField(source='gst')
    end_use_sales_discount = serializers.IntegerField(source='sales_discount')
    limited_stock_status = serializers.SerializerMethodField()
    out_of_stock_status = serializers.SerializerMethodField()
    super_distributor_rate =serializers.DecimalField(source='super_distributer_price',max_digits=10,   decimal_places=2)
    category_id_old = serializers.SerializerMethodField()
    sub_category_id_old = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    sub_category = serializers.SerializerMethodField()
    product_images = MobileProductImageSerializer(many=True, required = False, source='images')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    is_favourite = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    
    def get_product_name(self, obj):
        lang = self.context.get('lang', 'en')
        if lang == 'en':
            return obj.name
        translation = obj.translations.filter(language_code__iexact=lang).first()
        return translation.name if translation and translation.name else obj.name

    def get_short_name(self, obj):
        lang = self.context.get('lang', 'en')
        if lang == 'en':
            return obj.short_name
        translation = obj.translations.filter(language_code__iexact=lang).first()
        return translation.short_name if translation and translation.short_name else obj.short_name

    def get_feature(self, obj):
        lang = self.context.get('lang', 'en')
        if lang == 'en':
            return obj.feature
        translation = obj.translations.filter(language_code__iexact=lang).first()
        return translation.feature if translation and translation.feature else obj.feature

    def get_description(self, obj):
        # original fallback behavior
        if not obj.description or not obj.description.strip():
            return None

        lang = self.context.get('lang', 'en')
        if lang == 'en':
            return obj.description

        translation = obj.translations.filter(language_code__iexact=lang).first()
        return translation.description if translation and translation.description else obj.description
       
    def get_limited_stock_status(self, obj):
        return 1 if str(obj.limited_stock).lower() in ["yes", "true", "1"] else 0

    def get_out_of_stock_status(self, obj):
        return 1 if str(obj.out_of_stock).lower() in ["yes", "true", "1"] else 0
    
    def get_category_id_old(self,obj):
        first_category = obj.category.values_list('id', flat=True).first()
        return first_category
    
    def get_sub_category_id_old(self, obj):
        first_category = obj.sub_category.values_list('id', flat=True).first()
        return first_category
        
    def get_category(self, obj):
        return ", ".join([cat.name for cat in obj.category.all()]) if obj.category.exists() else ""

    def get_sub_category(self, obj):
        return ", ".join([sub.name for sub in obj.sub_category.all()]) if obj.sub_category.exists() else ""
        
    def get_is_favourite(self, obj):
        request = self.context.get("request")
        user_id = None
        if request:
            user_id = request.data.get("user_id") if hasattr(request, "data") else None

            # If user_id is invalid/null → fallback to token user
            if not user_id or str(user_id).lower() in ["", "null", "none"]:
                if hasattr(request, "user") and request.user.is_authenticated:
                    user_id = request.user.id
                else:
                    return 'false'
        
        return 'true' if obj.favouritemodel_set.filter(user_id=user_id).exists() else 'false'

    def get_stock(self,obj):
        inventory = Inventory.objects.filter(product = obj).first()
        if inventory:
            return inventory.quantity
        else:
            return 0
    class Meta:
        model = ProductModel
        fields = ['id','category_id_old','sub_category_id_old','product_name','stock','distributer_price','retailer_price','product_price','description','brand_id','is_favourite','item_code','group','model','color','company_code','unit','hsn_code','upc_barcode',
                  'lan_barcode','barcode_image','super_distributor_rate','gst_percentage','end_use_sales_discount','warranty','feature','weight','document','web_link','video_link','short_name','limited_stock_status','out_of_stock_status','created_at','updated_at',
                  'category','sub_category','product_images']

class ProductImportSerializer(serializers.Serializer):
    file = serializers.FileField()

