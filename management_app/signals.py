from django.db.models.signals import pre_save
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from management_app.models import Cart, OrderModel, PurchaseOrder
from googletrans import Translator
from .models import ProductModel, ProductTranslation,HomeCategoryModel, HomeCategoryTranslation, CategoryModel, CategoryTranslation, OrderLinesModel, Inventory, PurchaseOrderItem
from user_app.models import Notification
from user_app.Sms.Sms_service import MSG91Service2
from rest_framework.exceptions import ValidationError
import os

@receiver(post_save, sender=Cart)
def my_receiver_function(sender, instance, created, **kwargs):
    if created:
        # Set price based on role
        if instance.product and instance.price == 0.0:
            if instance.user and instance.user.role:
                role_type = instance.user.role.type
                if role_type == "Retailer" and instance.product.retailer_price:
                    instance.price = float(instance.product.retailer_price)
                elif role_type == "Wholesaler" and instance.product.distributer_price:
                    instance.price = float(instance.product.distributer_price)
                elif role_type == "Distributer" and instance.product.distributer_price:
                    instance.price = float(instance.product.distributer_price)
                else:
                    instance.price = float(instance.product.product_price)
            else:
                instance.price = float(instance.product.product_price)

        # Set brand from product
        if instance.product:
            instance.brand = instance.product.brand

        # Handle discount safely
        try:
            instance.discount = float(instance.discount or 0)
        except ValueError:
            instance.discount = 0

        # Calculate discount price
        if instance.discount > 0:
            instance.discount_price = round(instance.price - (instance.price * instance.discount / 100), 2)
        else:
            instance.discount_price = instance.price

        # Save without re-triggering the signal infinitely
        Cart.objects.filter(pk=instance.pk).update(
            price=instance.price,
            brand=instance.brand,
            discount=instance.discount,
            discount_price=instance.discount_price
        )
    else:
        print(f"Cart instance updated: {instance.pk}")
        

def generate_sequence_id(model, field_name, prefix_code):
    """
    Generate sequence like: SGS/SO/2025/000001 or SGS/PO/2025/000001
    """
    current_year = datetime.now().year
    prefix = f"SGS/{prefix_code}/{current_year}/"

    last_obj = model.objects.filter(**{f"{field_name}__startswith": prefix}).order_by('id').last()

    if last_obj:
        last_sequence = int(getattr(last_obj, field_name).split('/')[-1])
    else:
        last_sequence = 0

    new_sequence = str(last_sequence + 1).zfill(6)
    return f"{prefix}{new_sequence}"


@receiver(pre_save, sender=OrderModel)
def generate_order_id(sender, instance, **kwargs):
    if not instance.order_id:
        instance.order_id = generate_sequence_id(OrderModel, "order_id", "SO")

@receiver(pre_save, sender=PurchaseOrder)
def generate_purchase_id(sender, instance, **kwargs):
    if not instance.purchase_id:
        instance.purchase_id = generate_sequence_id(PurchaseOrder, "purchase_id", "PO")
    
    if not instance.pk:
        return  # new order, no check

    try:
        old_instance = PurchaseOrder.objects.get(pk=instance.pk)
    except PurchaseOrder.DoesNotExist:
        return

    old_status = old_instance.order_status
    new_status = instance.order_status

    # If already Purchase Order, do NOT allow status change
    if old_status == "Purchase Order" and new_status != old_status:
        raise ValidationError(
            {"Purchased Order": "Order is already confirmed and status cannot be changed."}
        )


@receiver(post_save, sender=PurchaseOrder)
def update_inventory_after_purchase_order(sender, instance, created, **kwargs):

    # Only run when status is Purchase Order
    if instance.order_status != "Purchase Order":
        return

    # Fetch items
    purchase_items = PurchaseOrderItem.objects.filter(purchase_order=instance)

    for item in purchase_items:
        try:
            inventory = Inventory.objects.get(product_id=item.product.id)
            inventory.quantity += item.quantity
            inventory.save()
        except Inventory.DoesNotExist:
            raise ValidationError(
                {'inventory': f'Inventory with id {item.product.id} does not exist.'}
            )

LANGUAGES = ['hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa'] 

TRANSLATABLE_FIELDS = ['name', 'description']

@receiver(pre_save, sender=ProductModel)
def handle_product_changes(sender, instance, **kwargs):
    """
    Single pre_save signal that:
    1. Deletes translations if any translatable field changed
    2. Deletes barcode image if item_code, product_price, or short_description changed
    3. Marks barcode for regeneration after save
    """
    if not instance.pk:
        return

    old_product = ProductModel.objects.filter(pk=instance.pk).first()
    if not old_product:
        return

    # Delete translations if translatable field changed
    if any(
        getattr(old_product, field) != getattr(instance, field)
        for field in TRANSLATABLE_FIELDS
    ):
        ProductTranslation.objects.filter(product=instance).delete()

    # Watch fields for barcode regeneration
    watched_fields = ['item_code', 'product_price', 'short_description']
    if any(
        getattr(old_product, field) != getattr(instance, field)
        for field in watched_fields
    ):
        # Delete old barcode image safely
        if old_product.barcode_image and old_product.barcode_image.path and os.path.isfile(old_product.barcode_image.path):
            try:
                os.remove(old_product.barcode_image.path)
            except Exception:
                pass

        instance.barcode_image = None
        instance._barcode_needs_regen = True
        
@receiver(post_save, sender=ProductModel)
def handle_product_post_save(sender, instance, created, **kwargs):
    """
    Handles:
       Regenerates barcode if flagged.
       Creates translations for all languages if missing.
    """
    # Regenerate barcode if flagged
    if getattr(instance, '_barcode_needs_regen', False):
        instance._barcode_needs_regen = False
        instance.save()

    # Create translations if missing
    translator = Translator()
    
    for lang in LANGUAGES:
        if ProductTranslation.objects.filter(product=instance, language_code=lang).exists():
            continue  # Skip existing translations

        try:
            ProductTranslation.objects.create(
                product=instance,
                language_code=lang,
                name=translator.translate(instance.name or "", src='en', dest=lang).text if instance.name else "",
                short_name=translator.translate(instance.short_name or "", src='en', dest=lang).text if instance.short_name else "",
                feature=translator.translate(instance.feature or "", src='en', dest=lang).text if instance.feature else "",
                description=translator.translate(instance.description or "", src='en', dest=lang).text if instance.description else "",
            )
        except Exception as e:
            print(f"❌ Error translating '{instance.name}' in '{lang}': {e}")
            
            
@receiver(pre_save, sender=HomeCategoryModel)
def delete_homecategory_translations_if_name_changed(sender, instance, **kwargs):
    if instance.pk:
        old_instance = HomeCategoryModel.objects.filter(pk=instance.pk).first()
        if old_instance and old_instance.name != instance.name:
            HomeCategoryTranslation.objects.filter(home_category=instance).delete()

@receiver(post_save, sender=HomeCategoryModel)
def create_homecategory_translations(sender, instance, created, **kwargs):
    translator = Translator()
    for lang in LANGUAGES:
        if HomeCategoryTranslation.objects.filter(home_category=instance, language_code=lang).exists():
            continue
        try:
            translated_text = translator.translate(instance.name or "", src='en', dest=lang).text
            HomeCategoryTranslation.objects.create(
                home_category=instance,
                language_code=lang,
                name=translated_text
            )
        except Exception as e:
            print(f"❌ Error translating HomeCategory '{instance.name}' to '{lang}': {e}")


@receiver(pre_save, sender=CategoryModel)
def delete_category_translations_if_name_changed(sender, instance, **kwargs):
    if instance.pk:
        old_instance = CategoryModel.objects.filter(pk=instance.pk).first()
        if old_instance and old_instance.name != instance.name:
            CategoryTranslation.objects.filter(category=instance).delete()

@receiver(post_save, sender=CategoryModel)
def create_category_translations(sender, instance, created, **kwargs):
    translator = Translator()
    for lang in LANGUAGES:
        if CategoryTranslation.objects.filter(category=instance, language_code=lang).exists():
            continue
        try:
            translated_text = translator.translate(instance.name or "", src='en', dest=lang).text
            CategoryTranslation.objects.create(
                category=instance,
                language_code=lang,
                name=translated_text
            )
        except Exception as e:
            print(f"❌ Error translating Category '{instance.name}' to '{lang}': {e}")


_old_status_cache = {}

@receiver(pre_save, sender=OrderModel)
def cache_old_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = OrderModel.objects.get(pk=instance.pk)
            _old_status_cache[instance.pk] = old_instance.order_status
        except OrderModel.DoesNotExist:
            _old_status_cache[instance.pk] = None
        
@receiver(post_save, sender=OrderModel)
def order_status_notification(sender, instance, created, **kwargs):
    if created:
        # New order → always notify
        title = f"New Order Created: {instance.order_id or instance.id}"
        customer_name = (
            f"{instance.customer.first_name} {instance.customer.last_name}"
            if instance.customer else "Unknown Customer"
        )
        body = f"A new order has been placed by {customer_name}."

        Notification.objects.create(
            title=title,
            body=body,
            user_id=instance.sales_person.id if instance.sales_person else None,
            customer_id=instance.customer.id if instance.customer else None,
        )
        return

    # Updated order → compare with cached status
    old_status = _old_status_cache.pop(instance.pk, None)
    if old_status and old_status != instance.order_status:
        title = f"Order Updated: {instance.order_id or instance.id}"
        body = f"Order status changed from '{old_status.title()}' to '{instance.order_status.title()}'."

        Notification.objects.create(
            title=title,
            body=body,
            user_id=instance.sales_person.id if instance.sales_person else None,
            customer_id=instance.customer.id if instance.customer else None,
        )


@receiver(post_save, sender=OrderModel)
def send_sms_on_order_creation(sender, instance, created, **kwargs):
    if created:
        try:
            if instance.pay_type == 'cod':
                msg_service = MSG91Service2(authkey='351148ALYt1r4ponc5ff55ba1P1')
                
                # Define the template for Cash on Delivery payment type
                cod_template_id = '670770f8d6fc0568146a0f72'
                
                # Get customer mobile number
                customer_mobile = str(instance.customer.mobile_no).replace('+', '').strip()
                print(f"Customer Mobile (COD): {customer_mobile}")
                
                # Send the SMS
                response = msg_service.send_message(
                    template_id=cod_template_id,
                    mobiles=customer_mobile,
                    var1=instance.order_id,
                    var2=instance.final_total
                )
                
                # Log the response or handle errors if necessary
                print(f"SMS Response (COD): {response}")

            elif instance.pay_type == 'online':
                msg_service = MSG91Service2(authkey='351148ALYt1r4ponc5ff55ba1P1')
                
                # Define the template for Online Payment type
                online_template_id = '663340d3d6fc057be424df73'
                
                # Get customer mobile number
                customer_mobile = str(instance.customer.phone_no)
                
                # Send the SMS
                response = msg_service.send_message(
                    template_id=online_template_id,
                    mobiles=customer_mobile,
                    var1=instance.order_id,
                    var2=instance.final_total
                )
                
                # Log the response or handle errors if necessary
                print(f"SMS Response (Online Payment): {response}")

        except Exception as e:
            # Log the exception and pass without raising an error
            print(f"An error occurred while sending SMS: {e}")
            pass
        
@receiver(post_save, sender=OrderModel)
def handle_inventory_on_order_status(sender, instance, **kwargs):
    """
    Reduce inventory only if:
    - Order status is 'delivered'
    - Salesperson is NOT a wholesaler
    """
    order = instance
    sales_person = getattr(order, "sales_person", None)
    role_type = str(getattr(getattr(sales_person, "role", None), "type", "")).strip().lower()

    if order.order_status.lower() == "out for delivery" and role_type != "wholesaler":
        order_lines = OrderLinesModel.objects.filter(order=order)
        for line in order_lines:
            product = line.product
            qty = float(line.quantity or 0)

            inv = Inventory.objects.filter(product=product).first()
            if not inv:
                inv = Inventory.objects.create(
                    product=product,
                    quantity=0 
                )
                print(
                    f"[Inventory] Created new inventory for {product.name} ")

            old_qty = inv.quantity
            inv.quantity = inv.quantity - qty
            inv.save()

            print(f"[Inventory] Reduced for {product.name} | Old: {old_qty} | New: {inv.quantity}")
    else:
        print(f"[Inventory] No reduction for Order {order.id} | Status: {order.order_status} | Salesperson Type: {role_type}")