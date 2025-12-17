from rest_framework.response import Response
from rest_framework import serializers
from ..models import *
from ..serializer.ProductSerializer import MobileProductSerializer
from management_app.serializer.ContactSerializer import SalesPersonSerializer

class OrderSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    customer = serializers.SerializerMethodField()
    company_pdf = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    def get_customer(self, obj):
        customer = obj.customer
        if not customer:
            return ""

        if customer.firm_name != "":
            return customer.firm_name

        return f"{customer.first_name} {customer.last_name}"


    def get_company_pdf(self, obj):
        # 1. Get all companies referenced in this order (SINGLE QUERY)
        order_company_ids = (
            OrderLinesModel.objects
            .filter(order=obj, product__company__isnull=False)
            .values_list("product__company_id", flat=True)
            .distinct()
        )

        order_company_ids = set(order_company_ids)

        # 2. Build response for all companies (SINGLE QUERY)
        data = [
            {
                "id": company.id,
                "name": company.name,
                "is_pdf": company.id in order_company_ids
            }
            for company in CompanyModel.objects.all()
        ]

        return data

    
    def get_is_admin(self,obj):
        request = self.context.get('request')
        if request.user.role.type == 'Admin':
            return True
        return False


    class Meta:
        model = OrderModel
        fields = ['id','customer','order_id','final_total','created_at','order_status','is_downloaded','is_admin','pay_type','order_type','company_pdf']


class MobileOrderLineSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id')
    qty = serializers.FloatField(source='quantity')
    price = serializers.FloatField(source='selling_price')
    total_price = serializers.FloatField(source='product_total')
    user_id = serializers.CharField(source='order.customer.id', read_only=True)
    brand_id = serializers.IntegerField(source='order.brand_id.id', read_only=True)
    order_id = serializers.CharField(source='order.id', read_only=True)
    order_number = serializers.CharField(source='order.order_id', read_only=True)
    paid_amount = serializers.CharField(source='order.paid_amount', read_only=True)
    shipping_address = serializers.CharField(source='order.shipping_address', read_only=True)
    remark = serializers.CharField(source='order.remark', read_only=True)
    order_status = serializers.CharField(source='order.order_status', read_only=True)
    recived_order_status = serializers.CharField(source='order.recived_order_status', read_only=True)
    tracking_link = serializers.CharField(source='order.tracking_link', read_only=True)
    tracking_number = serializers.CharField(source='order.tracking_number', read_only=True)
    created_at = serializers.DateTimeField(source='order.created_at', format="%Y-%m-%d %H:%M:%S",read_only=True)
    updated_at = serializers.DateTimeField(source='order.updated_at',format="%Y-%m-%d %H:%M:%S", read_only=True)
    deleted_at = serializers.DateTimeField(source='order.deleted_at',format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = OrderLinesModel
        fields = [
            "id", "user_id", "product_id", "brand_id", "order_id","order_number", "qty", "price",'discount','discount_price', "total_price","paid_amount", "order_status",
            "shipping_address","remark", "recived_order_status", "tracking_link", "tracking_number",
            "created_at", "updated_at", "deleted_at"
        ]

        
class MobileOrderSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="customer.id", read_only=True)
    payment_type = serializers.CharField(source="pay_type", read_only=True)
    total_price = serializers.CharField(source="final_total", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    deleted_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    order_number = serializers.CharField(source='order_id')
    class Meta:
        model = OrderModel
        fields = [
            "id",
            "user_id",
            "recieved_id",
            "order_number",
            "total_price",  
            "order_status",
            "shipping_address",
            "delivery_status",
            "pod_number",
            "remark",
            "review_status",
            "payment_type",    
            "transaction_id",
            "main_price",
            "percentage_off",
            'advance_amount',
            'balance_amount',
            'paid_amount',
            'is_draft',
            "created_at",
            "updated_at",
            "deleted_at",
        ]
   
class MobileProductOrderSerializer(serializers.ModelSerializer):
    product = MobileProductSerializer(read_only=True)
    user_id = serializers.IntegerField(source='order.customer.id', read_only=True) 
    brand_id = serializers.IntegerField(source='order.brand_id.id', read_only=True)  
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_number = serializers.CharField(source='order.order_id', read_only=True)
    qty = serializers.CharField(source='quantity')
    product_id = serializers.IntegerField(source='product.id')
    price = serializers.FloatField(source='selling_price')
    shipping_address = serializers.CharField(source='order.shipping_address', read_only=True)
    order_status = serializers.CharField(source='order.order_status', read_only=True)
    recived_order_status = serializers.CharField(source='order.recived_order_status', read_only=True)
    tracking_link = serializers.CharField(source='order.tracking_link', read_only=True)
    tracking_number = serializers.CharField(source='order.tracking_number', read_only=True)
    total_price = serializers. CharField(source= 'selling_price')
    created_at = serializers.DateTimeField(source='order.created_at', format="%Y-%m-%d %H:%M:%S",read_only=True)
    updated_at = serializers.DateTimeField(source='order.updated_at',format="%Y-%m-%d %H:%M:%S", read_only=True)
    deleted_at = serializers.DateTimeField(source='order.deleted_at',format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = OrderLinesModel
        fields = ['id', 'user_id', 'product_id', 'brand_id', 'order_id', 'order_number', 'qty', 'price', 'total_price', 'order_status', 'shipping_address', 'recived_order_status', 'tracking_link', 'tracking_number', 'created_at', 'updated_at', 'deleted_at', 'product']
     
class MobileOrderDetailSerializer(serializers.ModelSerializer):
    total_price = serializers.CharField(source="final_total", read_only=True)
    product_order = serializers.SerializerMethodField()
    user_id = serializers.CharField(source="customer.id", read_only=True)
    order_number = serializers.CharField(source='order_id')
    sales_person_detail = SalesPersonSerializer(source='sales_person', read_only=True)
    class Meta:
        model = OrderModel
        fields = ['id','user_id','sales_person_detail','order_number', 'total_price', 'order_status', 'review_status', 'shipping_address', 'remark', 'transaction_id', 'product_order']
        
    def get_product_order(self, obj):
        lang = self.context.get('lang', 'en')
        qs = OrderLinesModel.objects.filter(order=obj)
        return MobileProductOrderSerializer(qs, many=True, context={'lang': lang}).data
    
class MobileOrderLineCreateUpdateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id')
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    qty = serializers.FloatField(source='quantity')
    price = serializers.FloatField(source='selling_price')
    total_price = serializers.FloatField(source='product_total', read_only=True)
    user_id = serializers.CharField(source='order.customer.id', read_only=True)
    brand_id = serializers.IntegerField(source='order.brand_id.id', read_only=True)
    stock = serializers.SerializerMethodField()
    gst = serializers.SerializerMethodField()

    def get_gst(self, obj):
        if obj.product and hasattr(obj.product, 'gst'):
            return float(obj.product.gst)
        return 0.0

    def get_product_image(self, obj):
        if hasattr(obj.product, 'images') and obj.product.images.exists():
            first_image = obj.product.images.first()
            if first_image and first_image.image:
                return self.context['request'].build_absolute_uri(first_image.image.url)
        return None
    
    def get_stock(self,obj):
        inventory = Inventory.objects.filter(product = obj.product).first()
        if inventory:
            return inventory.quantity
        else:
            return 0
    class Meta:
        model = OrderLinesModel
        fields = [
            "id",
            "order",
            "product_id",
            "product_name",
            "product_image",
            'stock',
            'gst',
            "qty",
            "price",
            "discount",
            "discount_price",
            "total_price",
            "user_id",
            "brand_id",
        ]

    def create(self, validated_data):
        product_data = validated_data.pop("product")
        product = ProductModel.objects.get(id=product_data["id"])
        order = validated_data.get("order")

        quantity = validated_data.get("quantity", 0)
        selling_price = validated_data.get("selling_price", 0)
        discount = validated_data.get("discount", 0)

        # Calculate discount_price automatically
        discount_price = selling_price - (selling_price * discount / 100)
        validated_data["discount_price"] = discount_price

        # Check if product already exists in the order
        existing_line = OrderLinesModel.objects.filter(order=order, product=product).first()

        if existing_line:
            old_total = float(existing_line.product_total)
            # Update existing line quantity
            existing_line.quantity += quantity
            existing_line.selling_price = selling_price
            existing_line.discount = discount
            existing_line.discount_price = discount_price
            existing_line.product_total = existing_line.quantity * discount_price
            existing_line.save()
            
            new_total = float(existing_line.product_total)
            delta = new_total - old_total

            # Recalculate totals
            self.update_balance_delta(order, delta)
            self.update_order_totals(order)
            return existing_line

        # Otherwise, create a new line
        product_total = quantity * discount_price
        order_line = OrderLinesModel.objects.create(
            product=product,
            product_total=product_total,
            **validated_data
        )
        
        self.update_balance_delta(order, product_total)
        self.update_order_totals(order)
        return order_line

    def update(self, instance, validated_data):
        old_total = float(instance.product_total)
        product_data = validated_data.pop("product", None)
        if product_data:
            instance.product = ProductModel.objects.get(id=product_data["id"])

        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.selling_price = validated_data.get("selling_price", instance.selling_price)
        instance.discount = validated_data.get("discount", instance.discount)

        # Always recalculate discount_price
        instance.discount_price = instance.selling_price - (instance.selling_price * instance.discount / 100)

        instance.product_total = instance.quantity * instance.discount_price
        instance.save()
        
        new_total = float(instance.product_total)
        delta = new_total - old_total

        self.update_balance_delta(instance.order, delta)
        self.update_order_totals(instance.order)
        return instance
    
    def update_balance_delta(self, order, delta):
        delta = round(float(delta), 2)
        customer = order.customer  

        if order.advance_amount:
            # If advance paid → always maintain final_total - advance
            remain = float(order.advance_amount) - delta
            if remain > 0:
                order.advance_amount = remain
            else:
                order.advance_amount=0
                order.balance_amount += remain
        else:
            # Normal balance update
            order.balance_amount = (order.balance_amount or 0) + delta

        order.save()
        
        print(order.customer.advance_amount)
        if order.customer.advance_amount:
            extra = float(order.customer.advance_amount) - delta
            if extra > 0:
                order.customer.advance_amount = extra
            else:
                order.customer.advance_amount = 0
                order.customer.unpaid_amount += extra
        else:
            order.customer.unpaid_amount = (order.customer.unpaid_amount or 0) + delta

    def update_order_totals(self, order):
        order_lines = OrderLinesModel.objects.filter(order=order)

        # Calculate totals from order lines
        product_total = sum(float(line.product_total or 0) for line in order_lines)  # already discounted price
        product_total = round(product_total, 2)

        # Sum of all line discounts
        total_discount = sum((float(line.selling_price or 0) - float(line.discount_price or 0)) * float(line.quantity or 0) for line in order_lines)
        total_discount = round(total_discount, 2)
        
        total_discount_percentage = sum(float(line.discount_price or 0) * float(line.quantity or 0) for line in order_lines)
        total_discount_percentage = round(total_discount_percentage, 2)

        # Delta for balance adjustment
        previous_total = float(order.product_total or 0)
        delta = product_total - previous_total

        # Update order fields
        order.product_total = product_total
        order.percentage_off = total_discount_percentage
        order.discount_amt = total_discount  # update discount_amt from orderlines
        order.main_price = product_total + total_discount  # if main_price is before discount
        order.final_total = product_total + round(float(order.tax_amt or 0), 2) + round(float(order.shipping_amt or 0), 2)

        order.save()