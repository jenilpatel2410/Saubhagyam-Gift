from rest_framework import serializers
from management_app.models import OrderLinesModel
from django.db import models
from django.utils.text import slugify
from ..models import *
from datetime import datetime
from num2words import num2words
from user_app.models import UserModel

class WebOrderSerializer(serializers.ModelSerializer):
    product_name =  serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()
    main_order_id= serializers.SerializerMethodField()
    unit_price = serializers.DecimalField(source='selling_price',max_digits=10,decimal_places=2)
    total_price = serializers.DecimalField(source='product_total',max_digits=10,decimal_places=2)
    # category_slug = serializers.SerializerMethodField()
    # sub_category_slug = serializers.SerializerMethodField()
    shipping_address = serializers.CharField(source='order.shipping_address', read_only=True)
    order_status = serializers.CharField(source='order.order_status', read_only=True)  
    pay_type = serializers.CharField(source='order.pay_type', read_only=True)
    order_total = serializers.FloatField(source='product_total', read_only=True)
    order_date = serializers.DateTimeField(source='order.created_at',format="%Y-%m-%d %H:%M:%S",read_only=True)
    encrypted_id = serializers.CharField(source='product.encrypted_id',read_only=True)

    def get_product_name(self,obj):
        # return obj.product.name if obj.product else "Product not found"
        lang = self.context.get('lang', 'en')
        product = obj.product

        if lang == 'en':
            return product.name
        
        translation = ProductTranslation.objects.filter(product=product, language_code=lang).first()
        if translation and translation.name:
            return translation.name

        return product.name
    
    def get_image(self,obj):
        request = self.context.get('request')
        first_image = ProductImageModel.objects.filter(product=obj.product).order_by('id').first()
        if first_image and first_image.image:
            url = first_image.image.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_quantity(self,obj):
        return obj.quantity if obj.quantity else ''
    
    def get_order_id(self,obj):
        return obj.order.order_id if obj.order else "Order not found"

    def get_main_order_id(self,obj):
        return obj.order.id if obj.order else "Order not found"
    
    # def get_category_slug(self,obj):
    #     if obj.product.category:
    #        return slugify(obj.product.category.get_parent().name)
    #     return ""

    # def get_sub_category_slug(self,obj):
    #     if obj.product.category:
    #         if obj.product.category.name == 'Raksha Bandhan':
    #             return f"{obj.product.category.name.lower().replace(' ','')}"
    #         else:
    #             return f"{obj.product.category.name.lower().replace(' ','-')}"
    #     return ""

    class Meta:
        model = OrderLinesModel
        fields = ('id','main_order_id','order_id','product_name','image','quantity','unit_price','total_price','shipping_address','pay_type','order_status','order_total','order_date','encrypted_id')
        read_only_fields = fields
        
class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLinesModel
        fields = '__all__'

class PlaceOrderSerializer(serializers.ModelSerializer):
    rated_product_info = serializers.SerializerMethodField(read_only=True)
    total_in_words = serializers.SerializerMethodField(read_only=True)
    total_quantity = serializers.SerializerMethodField(read_only=True)
    product_data = serializers.SerializerMethodField(read_only=True)
    order_date_format = serializers.SerializerMethodField(read_only=True)
    expected_date_format = serializers.SerializerMethodField(read_only=True)
    order_lines = OrderLineSerializer(many=True, write_only=True)

    def get_order_date_format(self, obj):
        if obj.order_date:
            return datetime.strptime(str(obj.order_date), '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
        return ""

    def get_expected_date_format(self, obj):
        if obj.expiration_date:
            return datetime.strptime(str(obj.expiration_date), '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
        return ""

    def get_rated_product_info(self, obj):
        from django.contrib.auth.models import AnonymousUser
        request = self.context.get('request')

        if request.user and not isinstance(request.user, AnonymousUser) and isinstance(obj.id, int):
            contact_exist = UserModel.objects.filter(id=request.user.id)
            if contact_exist.exists():
                get_user = contact_exist.first()
                get_order = OrderModel.objects.filter(customer=get_user, id=obj.id)
                data_list = []

                for order in get_order:
                    for prod in order.product_info:
                        review_qs = ProductReviewModel.objects.filter(
                            user_id=request.user.id,
                            product_id=prod['product_id']
                        )
                        if review_qs.exists():
                            review = review_qs.first()
                            prod['product_rating_by_user'] = review.rating
                            prod['product_review'] = review.review
                            prod['is_rated'] = True
                        else:
                            prod['is_rated'] = False
                        data_list.append(prod)
                return data_list
        return None

    def get_product_data(self, obj):
        data = []
        if obj.product_info:
            for item in obj.product_info:
                prod_data = {
                    "product_name": item.get("product_name", ""),
                    "quantity": item.get("quantity", 0),
                    "tax_name": item.get("tax_name", ""),
                    "selling_price": item.get("selling_price", 0),
                    "total_amount": item.get("total_amount", 0),
                    "product_total": item.get("product_total", 0.0),
                    "sales_measurement_unit": item.get("sales_measurement_unit", "unit"),
                    "serialno": item.get("serialno", ""),
                    "serialno_name": item.get("serialno_name", ""),
                    "hsncode": "",
                    "inventory_serial": [],
                    "margin_amount": item.get("margin_amount", 0.0),
                    "after_margin_amount": item.get("after_margin_amount", item.get("selling_price", 0)),
                }
                try:
                    product_obj = ProductModel.objects.get(id=item["id"])
                    prod_data["hsncode"] = product_obj.hsn_code
                except Exception:
                    pass
                data.append(prod_data)
        return data

    def get_total_in_words(self, obj):
        try:
            return num2words(obj.final_total).capitalize()
        except ValueError as e:
            return str(e)

    def get_total_quantity(self, obj):
        return sum(float(i.get("quantity", 0)) for i in obj.product_info or [])


    class Meta:
        model = OrderModel
        fields = "__all__"

    def create(self, validated_data):
        order_lines_data = validated_data.pop("order_lines")
        order = OrderModel.objects.create(**validated_data)

        for line_data in order_lines_data:
            OrderLinesModel.objects.create(order=order, **line_data)

        return order