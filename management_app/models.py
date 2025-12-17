from django.db import models
from django.core.validators import (MaxLengthValidator, MinValueValidator, MaxValueValidator)
from django.db import models
from treebeard.mp_tree import MP_Node
from phonenumber_field.modelfields import PhoneNumberField
from tinymce_4.fields import TinyMCEModelField
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist,ValidationError
import base64
from user_app.models import UserModel,AddressModel
from datetime import date
import string
import barcode
from barcode.writer import ImageWriter
import os,re
import random
from datetime import datetime
from django.db.models import Max
from tinymce_4.fields import TinyMCEModelField
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Create your models here.

class CategoryTagsModel(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name
    class Meta:
        indexes = [
            models.Index(fields=['name'], name='idx_categorytag_name'),
        ]


class CategoryModel(MP_Node):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="Categories", blank=True, null=True)
    sub_category_image = models.ImageField(upload_to='Sub Categories',blank=True,null=True)
    is_active = models.BooleanField(default=True)
    sequence = models.IntegerField(unique=True , blank=True, null=True)
    full_pathtext = models.TextField(blank=True, null=True)
    category_tags = models.ForeignKey(CategoryTagsModel, on_delete=models.SET_NULL, blank=True, null=True)

    @property
    def encrypted_id(self):
        if self.id is None:
            return None
        return base64.urlsafe_b64encode(str(self.id).encode()).decode()

    @property
    def decrypted_id(self):
        if self.encrypted_id is None:
            return None
        return int(base64.urlsafe_b64decode(self.encrypted_id.encode()).decode())
    
    @property
    def full_path(self):
        ancestors_names = [ancestor.name for ancestor in self.get_ancestors()]
        self.full_pathtext = " / ".join([*ancestors_names, self.name])
        # self.save(update_fields=['full_pathtext'])        
        return " / ".join([*ancestors_names, self.name])


    @property
    def ancestor_names(self):
        return [ancestor.name for ancestor in self.get_ancestors()]
    

    def __str__(self):
        return f"{self.name} | {self.id}"

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        indexes = [
            models.Index(fields=['name'], name='idx_category_name'),
            models.Index(fields=['image'], name='idx_category_image'),
            models.Index(fields=['sequence'], name='idx_category_sequence'),
            models.Index(fields=['is_active'], name='idx_category_is_active'),
            models.Index(fields=['full_pathtext'], name='idx_category_full_pathtext'),
        ]
        
class CategoryTranslation(models.Model):
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE, related_name='translations')
    language_code = models.CharField(max_length=10) 
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('category', 'language_code')
        indexes = [
            models.Index(fields=['language_code'], name='idx_category_translation'),
        ]

    def __str__(self):
        return f"{self.name} ({self.language_code})"

class HomeCategoryModel(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Home Category"
        verbose_name_plural = "Home Categories"
        ordering = ['name']

    def __str__(self):
        return self.name
    
class HomeCategoryTranslation(models.Model):
    home_category = models.ForeignKey(HomeCategoryModel, on_delete=models.CASCADE, related_name='translations')
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('home_category', 'language_code')
        indexes = [
            models.Index(fields=['language_code'], name='idx_home_category_translation'),
        ]

    def __str__(self):
        return f"{self.name} ({self.language_code})"
    
class BrandModel(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="Brands",null=True,blank=True)
    number = models.IntegerField(null=True,blank=True)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'brand'
        verbose_name_plural = 'brands'
        indexes = [
            models.Index(fields=['name'], name='idx_Brand_name'),
        ]

class CompanyModel(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    address = models.ForeignKey('user_app.AddressModel', on_delete=models.SET_NULL , related_name = 'company',blank=True,null=True)
    logo = models.ImageField(upload_to='company_logos', blank=True, null=True)
    phone_no = PhoneNumberField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    gstin = models.CharField(max_length=15, verbose_name="GSTIN",help_text='GST Identification Number', blank=True, null=True)
    pan_number = models.CharField(verbose_name='PAN', max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.name} - {self.code}"
    
    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_company_name'),
            models.Index(fields=['code'], name='idx_company_code'),
            models.Index(fields=['is_active'], name='idx_company_is_active'),
            models.Index(fields=['gstin'], name='idx_company_gstin'),
            models.Index(fields=['pan_number'], name='idx_company_pan'),
        ]
        

class ProductTag(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=['name'], name='idx_producttag_name'),
        ]

class ProductModel(models.Model):
    PRODUCT_USE_TYPE_CHOICES = (('Consumable', 'Consumable'),
                                ('Service', 'Service'), ('Storable Product', 'Storable Product'), ('Voucher', 'Voucher'))
    PRODUCT_TYPE_CHOICES = (
        ('Single Product', 'Single Product'), ('Kit', 'Kit'))
 
    
    UNIT_CHOICES  = [
        ("pcs", "Piece"),
        ("set", "Set"),
        ("pair", "Pair"),
        ("box", "Box"),
        ("pack", "Pack"),
        ("dozen", "Dozen"),
        ("bundle", "Bundle"),
        ("roll", "Roll"),
        ("sheet", "Sheet"),
        ("book", "Book"),
        ("card", "Card"),
        ("bottle", "Bottle"),
        ("jar", "Jar"),
    ]

    category = models.ManyToManyField(CategoryModel, blank=True , related_name='product_single_category')
    sub_category = models.ManyToManyField(CategoryModel, blank=True , related_name='product_sub_category')
    home_categories = models.ManyToManyField(HomeCategoryModel, blank=True, related_name='home_categories')
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=100,choices=UNIT_CHOICES)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    product_price = models.DecimalField(
        default=0, verbose_name="MRP Rate(Product Price)", decimal_places=2, max_digits=10)
    image1 = models.ImageField(upload_to="Products", default="Products/product.png")
    item_code = models.CharField(max_length=100)
    group = models.CharField(max_length=100,null=True,blank=True)
    model = models.CharField(max_length=100,null=True,blank=True)
    color = models.CharField(max_length=100,null=True,blank=True)
    company = models.ForeignKey(CompanyModel,on_delete=models.SET_NULL,null=True,blank=True)
    warehouse_section = models.CharField(max_length=100,null=True,blank=True)
    company_code = models.CharField(max_length=100,null=True,blank=True)
    upc_barcode = models.CharField(
        max_length=13, blank=True, null=True, validators=[MaxLengthValidator(13)])
    lan_barcode = models.CharField(
        max_length=13, blank=True, null=True, validators=[MaxLengthValidator(13)])
    retailer_price = models.DecimalField(
        default=0, verbose_name="Retailer Price", decimal_places=2, max_digits=10,null=True,blank=True)
    distributer_price = models.DecimalField(
        default=0, verbose_name="Distributer Price", decimal_places=2, max_digits=10,null=True,blank=True)
    super_distributer_price = models.DecimalField(
        default=0, verbose_name="Super Distributer Price", decimal_places=2, max_digits=10,null=True,blank=True)
    purchase_price = models.DecimalField(
        default=0, verbose_name="Purchase Price", decimal_places=2, max_digits=10,null=True,blank=True)
    gst = models.FloatField(
        default=0, blank=True, null=True)
    sales_discount =models.FloatField(
        default=0, blank=True, null=True)
    warranty = models.CharField(max_length=10, null=True,blank=True)
    weight = models.FloatField(
        default=0, verbose_name='net weight (in gms)')
    web_link = models.URLField(blank=True, null=True)
    video_link = models.URLField(blank=True, null=True)
    feature = models.CharField(max_length=100, blank=True, null=True)
    description = TinyMCEModelField(null=True, blank=True)
    short_description = models.TextField(null=True,blank=True)
    limited_stock = models.CharField(max_length=10,choices=[
        ("Yes", "Yes"),
        ("No", "No"),], default='No')
    out_of_stock = models.CharField(max_length=10,choices=[
        ("Yes", "Yes"),
        ("No", "No"),], default= 'No')
    document = models.FileField(upload_to='Documents',null=True,blank=True)
    cost = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    image2 = models.ImageField(upload_to="Products", null=True, blank=True)
    image3 = models.ImageField(upload_to="Products", null=True, blank=True)
    image4 = models.ImageField(upload_to="Products", null=True, blank=True)
    image5 = models.ImageField(upload_to="Products", null=True, blank=True)
    product_use_type = models.CharField(
        max_length=255, choices=PRODUCT_USE_TYPE_CHOICES, default='')
    product_type = models.CharField(
        max_length=255, choices=PRODUCT_TYPE_CHOICES, default='')
    brand = models.ForeignKey(
        BrandModel, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(
        help_text='Notes for internal purposes', null=True, blank=True)
    barcode_image = models.ImageField(
        upload_to='Barcodes', blank=True, null=True)
    can_be_sold = models.BooleanField(default=True)
    can_be_purchased = models.BooleanField(default=True)
    hsn_code = models.CharField(max_length=255, null=True, blank=True)
    is_tracking  = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    is_favourite = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    product_tag = models.ManyToManyField(ProductTag, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    @property
    def encrypted_id(self):
        if self.id is None:
            return None
        return base64.urlsafe_b64encode(str(self.id).encode()).decode()

    @property
    def decrypted_id(self):
        if self.encrypted_id is None:
            return None
        return int(base64.urlsafe_b64decode(self.encrypted_id.encode()).decode())
    
    def generate_barcode_code(self):
        """Generate sequential numeric barcode based on date and category."""
        today_str = datetime.now().strftime("%Y%m%d")  # YYYYMMDD

        # Get last product for today
        latest = ProductModel.objects.filter(
            upc_barcode__startswith=today_str
        ).order_by('-upc_barcode').first()

        if latest and latest.upc_barcode:
            # Extract digits at the end
            match = re.search(r'(\d{5})$', latest.upc_barcode)
            last_seq = int(match.group(1)) if match else 0
            next_seq = last_seq + 1
        else:
            next_seq = 1

        barcode_number = f"{today_str}{next_seq:05d}" 
        return barcode_number

    def get_text_size(self,draw, text, font):
        """Helper to get width & height of text (works for all Pillow versions)."""
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:
            w, h = draw.textsize(text, font=font)
        return w, h

    def save(self, *args, **kwargs):


        if not self.upc_barcode :
            self.upc_barcode = self.generate_barcode_code()

        if not self.barcode_image and self.upc_barcode:

            writer_options = {
                'module_height': 3,
                'font_size': 7.1,
                'quiet_zone': 2,
                'text_distance': 2.7,
            }
            code128 = barcode.get('code128', self.upc_barcode, writer=ImageWriter())

            buffer = BytesIO()
            code128.write(buffer, options=writer_options)
            buffer.seek(0)

            # Open barcode image in PIL
            barcode_img = Image.open(buffer).convert("RGB")

            # ---- REMOVE BOTTOM BLANK SPACE ----
            # Convert to numpy for trimming
            import numpy as np
            np_img = np.array(barcode_img)

            # Find rows that are not fully white
            rows = np.where(np.mean(np_img, axis=2) < 250)[0]

            if len(rows) > 0:
                top = rows[0]
                bottom = rows[-1]
                barcode_img = barcode_img.crop((0, top, barcode_img.width, bottom))

            PADDING_TOP = 6        # adjust between 4–8 for your taste
            PADDING_BOTTOM = 5

            padded_height = barcode_img.height + PADDING_TOP + PADDING_BOTTOM
            canvas = Image.new("RGB", (barcode_img.width, padded_height), "white")
            canvas.paste(barcode_img, (0, PADDING_TOP))

            barcode_img = canvas

            # Create a new image with extra space on top for text
            extra_height = 60
            width, height = barcode_img.size
            new_img = Image.new("RGBA", (width, height + extra_height), "white")
            new_img.paste(barcode_img, (0, extra_height))

            # Draw text
            draw = ImageDraw.Draw(new_img)

            # Load font (fallback to default if not found)
            try:
                font_title = ImageFont.truetype("arialbd.ttf", 28)
                font_text = ImageFont.truetype("arial.ttf", 24)
            except:
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()

            # Text values
            item_text = f"{self.item_code}"
            price_text = f"1{int(self.product_price)}2" if self.product_price else f"1{int(self.retailer_price)}2"
            desc_text = self.short_description if self.short_description else ""

            # Calculate text positions
            item_w, item_h = self.get_text_size(draw,item_text, font_title)
            price_w, price_h = self.get_text_size(draw,price_text,font_text)
            desc_w, desc_h = self.get_text_size(draw,desc_text,font_text)

            # Item code (left) and short description (right) on the same line
            x_item = 30  # Left padding
            x_desc = width - desc_w - 30  # Right aligned
            y_offset = 1  # Top margin

            # Draw item code (left)
            draw.text((x_item, y_offset), item_text, fill="black", font=font_title)

            # Draw short description (right)
            draw.text((x_desc, y_offset), desc_text, fill="black", font=font_text)

            # Then move down for price or barcode
            y_offset += max(item_h, desc_h) + 10
            draw.text(((width - price_w) / 2, y_offset), price_text, fill="black", font=font_title)

            filename = f'{self.upc_barcode}.png'
            file_path = os.path.join('media/barcodes/', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            new_img.convert("RGB").save(file_path, "PNG")
            self.barcode_image.name = f'barcodes/{filename}'

        super().save(*args, **kwargs)
    

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "product"
        verbose_name_plural = "products"
        indexes = [
            models.Index(fields=['name'], name='idx_name'),
            models.Index(fields=['short_name'], name='idx_short_name'),
            models.Index(fields=['product_price'], name='idx_product_price'),
            models.Index(fields=['product_type'], name='idx_product_type'),
            models.Index(fields=['is_archived'], name='idx_is_archived'),
            models.Index(fields=['is_published'], name='idx_is_published'),
            models.Index(fields=['brand'], name='idx_brand'),
            models.Index(fields=['product_use_type'], name='idx_product_use_type'),
            models.Index(fields=['created_at'], name='idx_product_created_at'),
            models.Index(fields=['is_tracking'], name='idx_product_is_tracking'),
            models.Index(fields=['hsn_code'], name='idx_hsn_code'),
            models.Index(fields=['weight'], name='idx_weight'),
        ]
        
class ProductTranslation(models.Model):
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='translations')
    language_code = models.CharField(max_length=10)  
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    feature = models.CharField(max_length=255, blank=True, null=True)
    description = TinyMCEModelField(blank=True, null=True)

    class Meta:
        unique_together = ('product', 'language_code')
        indexes = [
            models.Index(fields=['language_code'], name='idx_product_translation'),
        ]

    def __str__(self):
        return f"{self.name} ({self.language_code})"

class ProductImageModel(models.Model):
    product = models.ForeignKey(ProductModel,on_delete=models.CASCADE,related_name='images')
    image = models.ImageField(upload_to="Products")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ['product__created_at']

    def __str__(self):
        return f"Image for {self.product.name}"
  
class NewsModel(models.Model):
   title = models.CharField(max_length=100)
   image = models.ImageField(null=True,blank=True)
   description = TinyMCEModelField(null=True, blank=True)
   role = models.ForeignKey('user_app.RoleModel',on_delete=models.CASCADE,null=True,blank=True)
   created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
   updated_at = models.DateTimeField(auto_now=True)
   deleted_at = models.DateTimeField(null=True, blank=True)
   is_active = models.BooleanField(default=True)

   class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["role"]),
        ]


class BusinessCategoryModel(models.Model):
    name= models.CharField(max_length=100)

    class Meta:
        verbose_name = "Business Category"
        verbose_name_plural = "Business Categories"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

class InquiryModel(models.Model):
    name = models.ForeignKey('user_app.UserModel',on_delete=models.CASCADE)
    product = models.ForeignKey(ProductModel,on_delete=models.CASCADE,null=True, blank= True)
    quantity = models.IntegerField(default=1)
    description = TinyMCEModelField(null=True, blank=True)
    status = models.CharField(max_length=30,choices=[
        ("Pending", "Pending"),
        ("Complete", "Complete")],null=True, blank=True)
    user = models.ForeignKey(UserModel,on_delete=models.CASCADE,related_name='user', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["name", "status"]),  # useful for filtering user inquiries by status
        ]


class FeedbackModel(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    title = models.CharField(max_length=200)
    description = TinyMCEModelField(null=True, blank=True)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.email}"


class HelpAndSupportModel(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    title = models.CharField(max_length=200)
    description = TinyMCEModelField(null=True, blank=True)

    class Meta:
        verbose_name = "Help & Support"
        verbose_name_plural = "Help & Support"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.email}"
    

class FirmModel(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey('user_app.UserModel',on_delete=models.CASCADE)

class ThirdPartyModel(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey('user_app.UserModel',on_delete=models.CASCADE)



class OrderModel(models.Model):
    ORDER_STATUS = (('pending', 'pending'), ('out for delivery',
                    'out for delivery'), ('delivered', 'delivered'), ('cancelled', 'cancelled'))
    ORDER_TYPE_CHOICES = (('Urgent', 'Urgent'), ('Regular', 'Regular'), ('Normal', 'Normal'))
    PAYMENT_TYPE_CHOICES = (
        ('cod', 'cod'),
        ('online', 'online'),
        ('paid', 'paid'),
        ('unpaid', 'unpaid'),
        ('half-paid', 'half-paid'),
        ('credit', 'credit'),
    )

    class SALES_STATUS_CHOICES(models.TextChoices):
        quotation = ('Quotation', 'Quotation')
        quotation_sent = ('Quotation Sent', 'Quotation Sent')
        sales_order = ('Sales Order', 'Sales Order')
        cancel_order = ('Cancelled', 'Cancelled')
    
    sales_person = models.ForeignKey('user_app.UserModel', on_delete=models.SET_NULL, blank=True, null=True, related_name='sales_person')
    customer = models.ForeignKey('user_app.UserModel', on_delete=models.SET_NULL,blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.CharField(max_length=255, blank=True, null=True)
    firm_name = models.ForeignKey(FirmModel,on_delete=models.SET_NULL,blank=True,null=True)
    third_party_order = models.ForeignKey(ThirdPartyModel,on_delete=models.SET_NULL,blank=True,null=True)
    product_info = models.JSONField(blank=True, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(blank=True, null=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    order_status = models.CharField(choices=ORDER_STATUS, default='pending', max_length=100)
    pay_type = models.CharField(max_length=200, choices=PAYMENT_TYPE_CHOICES, blank=True, null=True)
    order_type = models.CharField(max_length=100, choices=ORDER_TYPE_CHOICES, blank=True, null=True)
    sale_status = models.CharField(max_length=255, choices=SALES_STATUS_CHOICES.choices, default=SALES_STATUS_CHOICES.quotation)
    product_total = models.FloatField(default=0.00)
    discount = models.FloatField(default=0.00)       
    discount_amt = models.FloatField(default=0.00)
    tax = models.FloatField(default=0.00)
    tax_amt = models.FloatField(default=0.00)
    shipping_amt = models.PositiveIntegerField(default=0)
    final_total = models.FloatField(default=0.00)
    is_paid = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    is_gift = models.BooleanField(default=False, verbose_name="is a gift?")
    gift_message = models.TextField(blank=True, null=True, verbose_name="gift message")
    applied_voucher_code = models.CharField(max_length=25, blank=True, null=True)
    margin = models.IntegerField(default=0)
    is_ecommerce = models.BooleanField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    address = models.ForeignKey('user_app.AddressModel', on_delete= models.SET_NULL, blank=True,null=True)
    source_doc = models.CharField(max_length=255, blank=True, null=True)
    is_downloaded = models.BooleanField(default=False)
    
    brand_id = models.ForeignKey(BrandModel, on_delete=models.SET_NULL, null=True, blank=True)
    recieved_id = models.IntegerField(blank=True, null=True)
    delivery_status = models.CharField(choices=ORDER_STATUS, default='Pending', max_length=100)
    pod_number = models.CharField(max_length=255, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    review_status = models.CharField(max_length=50, default="pending")
    main_price = models.FloatField(default=0.00)
    percentage_off = models.FloatField(default=0.00)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    order_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    advance_amount = models.FloatField(default=0.00)
    balance_amount = models.FloatField(default=0.00)
    paid_amount = models.FloatField(default=0.00)
    is_draft = models.BooleanField(default=False)
    
    @property
    def total_order_qty(self):
        total_qt = 0
        for i in self.product_info:
            total_qt += i["quantity"]
        return total_qt

    @property
    def untax_amount(self):
        l1 = []
        amount = 0
        for i in self.product_info:
            
            if "untax_amount" in i:
                amount = i["untax_amount"]
                amount = i["untax_amount"] * i["quantity"]
    
        l1.append(amount)
        return sum(l1)

    class Meta:
        indexes = [
            models.Index(fields=['order_id'], name='idx_order_reference'),
            models.Index(fields=['order_date'], name='idx_order_date'),
            models.Index(fields=['final_total'], name='idx_final_total'),
            models.Index(fields=['is_paid'], name='idx_is_paid'),
            models.Index(fields=['is_expired'], name='idx_is_expired'),
            models.Index(fields=['is_gift'], name='idx_is_gift'),
            models.Index(fields=['gift_message'], name='idx_gift_message'),
            models.Index(fields=['applied_voucher_code'], name='idx_applied_voucher_code'),
            models.Index(fields=['margin'], name='idx_margin'),
            models.Index(fields=['is_ecommerce'], name='idx_is_ecommerce'),
            models.Index(fields=['note'], name='idx_note'),
            models.Index(fields=['source_doc'], name='idx_source_doc'),
            models.Index(fields=['created_at'], name='idx_order_created_at'),
            models.Index(fields=['order_status'], name='idx_order_status'),
            models.Index(fields=['delivery_date'], name='idx_delivery_date'),
            models.Index(fields=['expiration_date'], name='idx_expiration_date'),
            models.Index(fields=['pay_type'], name='idx_pay_type'),  
        ]

    def __str__(self):
        return f"{self.order_id} - {self.customer}"
    

class OrderLinesModel(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE , blank=True , null=True , related_name='orderrelation')
    product = models.ForeignKey(ProductModel, on_delete=models.SET_NULL , blank=True , null=True)
    quantity = models.FloatField(default=0.00)
    selling_price = models.FloatField(default=0.00)
    discount = models.FloatField(default=0.00)
    discount_price = models.FloatField(default=0.00)
    tax_amount = models.FloatField(default=0.00)
    untax_amount = models.FloatField(default=0.00)
    product_total = models.FloatField(default=0.00)
    margin_amount = models.FloatField(default=0.00)
    after_margin_amount = models.FloatField(default=0.00)

class LocationModel(models.Model):
    class LocationTypeChoices(models.TextChoices):
        vendor_location = ('Vendor Location', 'Vendor Location')
        view = ('View', 'View')
        internal_location = ('Internal Location', 'Internal Location')
        customer_location = ('Customer Location', 'Customer Location')
        inventory_loss = ('Inventory Loss', 'Innventory Loss')
        production = ('Production', 'Production')
        transit_location = ('Transit Location', 'Transit Location')

    class RemovalStrategyChoices(models.TextChoices):
        FIFO = ('First In First Out (FIFO)', 'First In First Out (FIFO)')
        LIFO = ('Last In First Out (LIFO)', 'Last In First Out (LIFO)')
        FEFO = ('First Expiry First Out (FEFO)','First Expiry First Out (FEFO)')

    location_name = models.CharField(max_length=255)
    parent_location = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    location_type = models.CharField(max_length=255, choices=LocationTypeChoices.choices)
    is_a_scrap_location = models.BooleanField(default=False)
    is_a_return_location = models.BooleanField(default=False)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    removal_strategy = models.CharField(max_length=255, choices=RemovalStrategyChoices.choices, blank=True, null=True)
    external_note = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.location_name
    
    class Meta:
        indexes = [
        ]

class SerialNumbersModel(models.Model):
    serial_no = models.CharField(max_length=255, blank=True, null=True)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, blank=True, null=True, related_name = 'serial')
    created_on = models.DateTimeField(default=timezone.now)
    best_before_date = models.DateTimeField(
        verbose_name="Best before Date", blank=True, null=True)
    removal_date = models.DateTimeField(
        verbose_name="Removal Date", blank=True, null=True)
    end_of_life = models.DateTimeField(
        verbose_name="End Of Life Date", blank=True, null=True)
    alert_time = models.DateTimeField(verbose_name="Alert Date", blank=True, null=True)
    is_repacked = models.BooleanField(default=False, verbose_name='Repacked')

    def __str__(self):
        return f"{self.serial_no} - {self.id}"
    
    class Meta:
        indexes = [
        ]



class Inventory(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    location_stock = models.ForeignKey(LocationModel, on_delete=models.CASCADE, blank=True, null=True)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0.0, verbose_name="On Hand Quantity")
    discount = models.FloatField(blank=True,null=True)
    counted_quantity = models.FloatField(default=0.0)
    reserved_quantity = models.FloatField(default=0.0)
    serialno = models.ForeignKey(SerialNumbersModel, on_delete=models.CASCADE, blank=True, null=True)
    sequence_no = models.IntegerField(unique=True, blank=True, null=True)

    @property
    def value(self):
        getproduct = ProductModel.objects.get(id=self.product.id)
        value = float(getproduct.retailer_price) * self.quantity
        return round(value, 2)


    @property
    def difference(self):
        difference = self.counted_quantity - self.quantity
        return difference



    def save(self, *args, **kwargs):
        # self.clean()
        if not self.sequence_no:
            last = Inventory.objects.order_by('-sequence_no').first()
            self.sequence_no = 1 if not last else last.sequence_no + 1

        self.quantity = round(self.quantity, 3)
        self.counted_quantity = round(self.counted_quantity, 3)
        self.reserved_quantity = round(self.reserved_quantity, 3)
        
        super(Inventory, self).save(*args, **kwargs) # Call the real save() method

    def __str__(self):
        return f"{self.product.name}-{self.id}"

    class Meta:
        indexes = [
            models.Index(fields=['created_at'], name='idx_inventory_created_at'),
            models.Index(fields=['product'], name='idx_inventory_product'),
            models.Index(fields=['location_stock'], name='idx_inventory_location'),
            models.Index(fields=['serialno'], name='idx_inventory_serialno'),
        ]
    
    def formatted_quantity(self):
        return f"{self.quantity:.3f}"
    formatted_quantity.short_description = 'On Hand Quantity'

    def formatted_counted_quantity(self):
        return f"{self.counted_quantity:.3f}"
    formatted_counted_quantity.short_description = 'Counted Quantity'

    def formatted_reserved_quantity(self):
        return f"{self.reserved_quantity:.3f}"
    formatted_reserved_quantity.short_description = 'Reserved Quantity'



class KYCDetailsModel(models.Model):
    firm_name = models.CharField(max_length=255)  # indexed
    incorporation_date = models.DateField(null=True, blank=True)
    business_category = models.ForeignKey(BusinessCategoryModel, on_delete=models.CASCADE,null=True, blank=True)
    company_logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)
    ho_address = models.TextField(null=True, blank=True)
    whatsapp_no = models.CharField(max_length=15, null=True, blank=True)
    fax = models.CharField(max_length=50, null=True, blank=True)
    tel = models.CharField(max_length=50, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    social_media_address = models.URLField(null=True, blank=True)
    pancard_no = models.CharField(max_length=20, null=True, blank=True, unique=True)
    gstin_no = models.CharField(max_length=20, null=True, blank=True, unique=True)
    tan_no = models.CharField(max_length=20, null=True, blank=True, unique=True)
    cin_no = models.CharField(max_length=21, null=True, blank=True, unique=True)
    sez_company = models.CharField(max_length=255, null=True, blank=True)
    csc_funding_company = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['firm_name']),
            models.Index(fields=['business_category']),
            models.Index(fields=['gstin_no']),
        ]
        verbose_name = "KYC Detail"
        verbose_name_plural = "KYC Details"

    def __str__(self):
        return self.firm_name


class BankDetailsModel(models.Model):
    kyc_detail = models.ForeignKey(KYCDetailsModel, on_delete=models.CASCADE, related_name="bank_details")
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50, unique=True)
    ifsc_code = models.CharField(max_length=20)
    branch_name = models.CharField(max_length=255, null=True, blank=True)
    account_holder_name = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['bank_name']),
            models.Index(fields=['account_number']),
            models.Index(fields=['ifsc_code']),
        ]
        verbose_name = "Bank Detail"
        verbose_name_plural = "Bank Details"

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

class VersionModel(models.Model):
    
    android_id=models.IntegerField()
    android_version = models.CharField(max_length=100)
    android_description =TinyMCEModelField(null=True,blank=True)
    android_status=models.CharField(max_length=30)
    
    ios_id=models.IntegerField()
    ios_version = models.CharField(max_length=100)
    ios_description =TinyMCEModelField(null=True,blank=True)
    ios_status=models.CharField(max_length=30)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return self.android_status

class OfferModel(models.Model):
    """Normal Offer"""
    DISCOUNT_TYPE_CHOICES = [
        ("flat", "Flat Discount"),
        ("percentage", "Percentage Discount"),
    ]
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="offers/",null=True,blank=True)   # 1280x1920 recommended
    roles = models.ForeignKey('user_app.RoleModel',on_delete=models.SET_NULL,null=True, blank=True, related_name="offers")
    
    coupon_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, null=True,blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  

    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    description = TinyMCEModelField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class OnlinePaymentOfferModel(models.Model):
    """Offer based on price range"""
    start_price = models.IntegerField()
    end_price = models.IntegerField()
    percentage_off = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)  # e.g. 12.50%

    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.start_price} - {self.end_price} ({self.percentage_off}% Off)"


class OfferSliderModel(models.Model):
    """Slider banners"""
    image = models.ImageField(upload_to="offer_sliders/",null=True,blank=True)   # 1080x500 recommended
    banner_number = models.PositiveIntegerField()
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True,blank=True)
 
    class Meta:
        ordering = ["banner_number"]  # always sorted by number
 
    def __str__(self):
        return f"Slider {self.banner_number}"

class FavouriteModel(models.Model):
    user_id = models.ForeignKey('user_app.UserModel', on_delete=models.CASCADE)
    product_id = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.status

class Cart(models.Model):
    STATUS_CHOICES = (
        (0, "In Cart"),  
        (1, "Ordered"),   
        (2, "Removed"),   
    )

    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="cart_items", null=True, blank=True
    )
    visitor = models.ForeignKey('user_app.VisitorModel', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name="product")
    brand = models.ForeignKey(BrandModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="brand")

    qty = models.PositiveIntegerField(default=1)
    price = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.00)
    discount_price = models.FloatField(default=0.00)

    status = models.IntegerField(choices=STATUS_CHOICES, default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # def save(self, *args, **kwargs):
    #     if self.product and self.price == 0.0:
    #         if self.user and self.user.role:
    #             if self.user.role.type == "Retailer" and self.product.retailer_price: 
    #                 self.price = float(self.product.retailer_price)
    #             elif self.user.role.type == "Wholesaler" and self.product.distributer_price: 
    #                 self.price = float(self.product.distributer_price)
    #             elif self.user.role.type == "Distributer" and self.product.distributer_price: 
    #                 self.price = float(self.product.distributer_price)
    #             else:
    #                 self.price = float(self.product.retailer_price)
    #         else:
    #             self.price = float(self.product.retailer_price)
        
    #     if self.product:
    #         self.brand = self.product.brand

    #     try:
    #         self.discount = float(self.discount or 0)
    #     except ValueError:
    #         self.discount = 0
            
    #     if self.discount > 0:
    #         self.discount_price = round(self.price - (self.price * self.discount / 100), 2)
    #     else:
    #         self.discount_price = self.price
    #     super().save(*args, **kwargs)

    @property
    def total_price(self):
        return round(self.discount_price * float(self.qty), 2)

    def __str__(self):
        return f"{self.product.name} ({self.qty})"
    
    class Meta:
        verbose_name = 'cart'
        verbose_name_plural = 'carts'


class OnlinePaymentOffer(models.Model):
    start_price_value = models.DecimalField(
        max_digits=12, decimal_places=2
    )
    end_price_value = models.DecimalField(
        max_digits=12, decimal_places=2
    )
    percentage_off = models.DecimalField(
        max_digits=5, decimal_places=2
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(
        null=True, blank=True
    )

    class Meta:
        verbose_name = 'Online payment offer'
        verbose_name_plural = 'Online payment offers'
        ordering = ['start_price_value']
        indexes = [
            models.Index(fields=['start_price_value'], name='idx_start_price_value'),
            models.Index(fields=['end_price_value'], name='idx_end_price_value'),
            models.Index(fields=['percentage_off'], name='idx_percentage_off'),
        ]

    def __str__(self):
        return f"Offer {self.start_price_value}-{self.end_price_value}: {self.percentage_off}%"

class PageModel(models.Model):
    PAGE_TYPES = [
        ("about us", "about us"),
        ("privacy policy", "privacy policy"),
        ("terms & conditions", "terms & conditions"),
    ]

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=PAGE_TYPES, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Page Model'
        verbose_name_plural = 'Page Models'
        indexes = [
            models.Index(fields=['title'], name='idx_title'),
            models.Index(fields=['type'], name='idx_type'),
        ]
    def __str__(self):
        return self.title
    
class PageTranslation(models.Model):
    page = models.ForeignKey('PageModel', on_delete=models.CASCADE, related_name='translations')
    language_code = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        unique_together = ('page', 'language_code')
        indexes = [
            models.Index(fields=['language_code'], name='idx_page_translation_lang'),
        ]

    def __str__(self):
        return f"{self.title} ({self.language_code})"
        
class Vendor(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Net 30"
    
    def __str__(self):
        return self.name

class ContactModel(models.Model):
    CONTACT_TYPE_CHOICES = (
        ('Individual', 'Individual'), ('Company', 'Company'))

    class ContactRoleChoices(models.TextChoices):
        customer = ('Customer', 'Customer')
        vendor = ('Vendor', 'Vendor')
        poscustomer = ('pos_customer', 'pos_customer')

    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(
        'user_app.UserModel', on_delete=models.CASCADE, blank=True, null=True)
    contact_type = models.CharField(
        max_length=10, choices=CONTACT_TYPE_CHOICES, default="Individual")
    contact_role = models.CharField(
        max_length=255, choices=ContactRoleChoices.choices, default=ContactRoleChoices.customer)
    name = models.CharField(max_length=255, blank=True, null=True)
    address = models.ForeignKey(
        'user_app.AddressModel', on_delete=models.SET_NULL, blank=True, null=True)
    many_address = models.ManyToManyField('user_app.AddressModel', blank=True ,related_name="contacts")     
    country = models.ForeignKey('user_app.CountryModel', on_delete=models.CASCADE, blank=True, null=True)    
    phone_no = PhoneNumberField(blank=True, null=True)
    another_phone_no = PhoneNumberField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(null=True, blank=True)
    mail_subscription_status = models.BooleanField(
        default=True, verbose_name='Mail Subscription', help_text='This will be unchecked if user unsubscribes from all mails.')
    gstin = models.CharField(max_length=255, verbose_name="GSTIN",
                             help_text='GST Identification Number', blank=True, null=True)
    pan_number = models.CharField(
        verbose_name='PAN', max_length=10, blank=True, null=True)
    transport = models.CharField(max_length=255, blank=True, null=True)
        
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f'{self.name} - {self.contact_role}'
    

    class Meta:
        verbose_name = 'contact'
        verbose_name_plural = 'contacts'
        indexes = [
            models.Index(fields=['user'], name='idx_contact_user'),
            models.Index(fields=['name'], name='idx_contact_name'),
            models.Index(fields=['created_at'], name='idx_created_at'),
            models.Index(fields=['contact_type'], name='idx_contact_type'),
            models.Index(fields=['contact_role'] , name='idx_contact_role'),
            models.Index(fields=['phone_no'] , name='idx_phone_no'),
            models.Index(fields=['email'] , name='idx_email'),
            models.Index(fields=['gstin'] , name='idx_gstin'),
            models.Index(fields=['pan_number'] , name='idx_pan_number'),
            models.Index(fields=['another_phone_no'] , name='idx_another_phone_no'),
            models.Index(fields=['is_active'] , name='idx_is_active'),
        ]


class PurchaseOrder(models.Model):
    class ORDER_STATUS(models.TextChoices):
        purchase_order = ('Purchase Order', 'Purchase Order')
        rfq = ('RFQ', 'RFQ')
        cancel = ('Cancelled', 'Cancelled')
    vendor = models.ForeignKey(ContactModel, on_delete=models.CASCADE, related_name="purchase_orders")
    order_date = models.DateTimeField(auto_now_add=True)
    purchase_address = models.ForeignKey('user_app.AddressModel', on_delete=models.CASCADE, verbose_name="Delivery Address",
                                         related_name="purchase_delivery_address", blank=True, null=True)
    expected_delivery = models.DateField(blank=True, null=True)
    sub_total = models.FloatField(default=0)
    order_status = models.CharField(choices=ORDER_STATUS.choices, default=ORDER_STATUS.rfq, max_length=100)
    payment_terms = models.TextField( blank=True, null=True)
    status_choices = [
        ("pending", "Pending"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default="pending")
    purchase_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    discount = models.FloatField(default=0.0) 
    discount_price = models.FloatField(default=0.0)
    final_total = models.FloatField(default=0.0)

    def calculate_totals(self):
        if self.discount > 0:
            self.discount_price = (self.sub_total * self.discount) / 100
        else:
            self.discount_price = 0

        self.final_total = self.sub_total - self.discount_price

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} | {self.vendor.name}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.FloatField(default=0.00)
    discount_price = models.FloatField(default=0.00)
    sub_total = models.FloatField(default=0)
    serial_no  = models.ForeignKey(SerialNumbersModel,on_delete=models.SET_NULL,blank=True,null=True)
    description = models.TextField(blank=True, null=True)
    
    @property
    def total_price(self):
        if self.quantity and self.unit_price:
            return float(self.quantity) * float(self.unit_price)
        return 0

    @property
    def total_after_discount(self):
        return self.total_price - self.discount_price

    def save(self, *args, **kwargs):
        # Calculate discount price automatically
        if self.discount > 0:
            self.discount_price = (self.total_price * self.discount) / 100
        else:
            self.discount_price = 0.0

        # Calculate sub_total if not manually set
        self.sub_total = self.total_price - self.discount_price

        super(PurchaseOrderItem, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class ProductReviewModel(models.Model):
    user = models.ForeignKey('user_app.UserModel', on_delete=models.SET_NULL, blank=True, null=True)
    product = models.ForeignKey(ProductModel, related_name='reviews' ,on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(5), MinValueValidator(1)])
    review = models.TextField(blank=True, null=True)
    published_at = models.DateTimeField(auto_now=True)

    @property
    def avg_rating_of_product(self):
        avg = ProductReviewModel.objects.filter(
            product__id=self.product.id).aggregate(avg_rating=models.Avg('rating'))
        return avg
    
class OnlinePaymentsModel(models.Model):
    txn_id = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.ForeignKey(OrderModel, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    status = models.BooleanField(blank=True, null=True)
    payment_datetime = models.DateTimeField()
    amount = models.FloatField(default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_mode = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['order_id'], name="idx_order_id"),
            models.Index(fields=['user'], name="idx_user"),
            models.Index(fields=['status'], name="idx_status"),
            models.Index(fields=['payment_datetime'], name="idx_payment_datetime")
            
        ]
        
class BlogModel(models.Model):
    title = models.CharField(max_length=255)
    banner = models.ImageField(upload_to='Blog_Banners')
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now=True)
    content = TinyMCEModelField()

    class Meta:
        verbose_name = 'blog'
        verbose_name_plural = 'blogs'
        ordering = ['-published_at']
        indexes = [ 
            models.Index(fields=['title'], name='idx_blog_title'),
            models.Index(fields=['published_at'], name='idx_blog_published_at'),
            models.Index(fields=['is_published'], name='idx_blog_is_published'),
            models.Index(fields=['banner'], name='idx_blog_banner')
        ]
    
    def __str__(self):
        return self.title
    
class Client(models.Model):
    name = models.CharField(max_length=255) 
    description = models.TextField()        
    image = models.ImageField(upload_to="Clientreview/", blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'client'
        verbose_name_plural = 'clients'
        ordering = ['-created_at']
        indexes = [ 
            models.Index(fields=['name'], name='idx_client_name'),
            models.Index(fields=['description'], name='idx_client_description'),
            models.Index(fields=['created_at'], name='idx_client_created_at'),
            models.Index(fields=['is_active'], name='idx_client_is_active'),
            models.Index(fields=['image'], name='idx_client_image')
        ]

    def __str__(self):
        return self.name
    
class ClientTranslation(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('client', 'language_code')
        verbose_name = 'Client Translation'
        verbose_name_plural = 'Client Translations'

    def __str__(self):
        return f"{self.name} ({self.language_code})"
    
class FeatureModel(MP_Node):
    name = models.CharField(
        max_length=50,
    )
    full_path = models.CharField(max_length=100,blank=True,null=True)
    component = models.CharField(max_length=100,blank=True,null=True)
    icon = models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=['name'], name='idx_feature_name'),
            models.Index(fields=['path'], name='idx_feature_path'),
        ]


class FeatureApplication(models.Model):
    role = models.ForeignKey(
        'user_app.RoleModel', on_delete=models.CASCADE, related_name="role_feature_permissions"
    )   
    feature = models.ForeignKey(FeatureModel,on_delete=models.CASCADE,null=True,blank=True)
    is_viewed = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    is_write = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    sequence_no = models.IntegerField(blank=True,null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['role'], name='idx_feature_role'),
            models.Index(fields=['is_viewed'], name='idx_feature_is_viewed'),
            models.Index(fields=['is_read'], name='idx_feature_read'),
            models.Index(fields=['is_write'], name='idx_feature_write'),
            models.Index(fields=['is_delete'], name='idx_feature_delete'),
        ]


    order_by = ['id']


# class BillModel(models.Model):
#     bill_id = models.CharField(
#         max_length=255, blank=True, null=True, verbose_name="bill_id", editable=False)
#     vendor = models.ForeignKey(
#         ContactModel, on_delete=models.CASCADE, blank=True, null=True)
#     delivery_address = models.ForeignKey(AddressModel, on_delete=models.CASCADE, verbose_name="Delivery Address",
#                                          related_name="bill_Delivery_address", blank=True, null=True)  # Foreign Key in Contact Model
#     reference = models.TextField(verbose_name="Reference", blank=True, null=True)
#     reference_note = models.TextField(verbose_name="Reference_note", blank=True, null=True)
#     source_doc = models.CharField(
#         max_length=255, blank=True, null=True, verbose_name="Source document")
#     bill_date = models.DateField(default=date.today, verbose_name="Bill Date")
#     account_date = models.DateField(
#         default=date.today, verbose_name="Accounting Date")
#     payment_date = models.DateField(
#         default=date.today, verbose_name="Payment date")
#     company = models.ForeignKey(CompanyModel, on_delete=models.CASCADE,blank=True, null=True)
    
#     payment_reference = models.CharField(
#         max_length=255, blank=True, null=True, verbose_name="Payment Reference")
#     created_by = models.ForeignKey(UserModel, on_delete=models.CASCADE, blank=True, null=True)
#     purchase = models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE,null=True, blank=True, related_name="bill_purchase_orders")
    
#     is_post = models.BooleanField(default=False)
#     is_cancelled = models.BooleanField(default=False)
#     total_amount = models.FloatField(default=0.00)
#     untax_amount = models.FloatField(default=0.00)
#     tax_amount = models.FloatField(default=0.00)
#     debit = models.FloatField(default=0.00)
#     credit = models.FloatField(default=0.00)
#     freight_charge = models.FloatField(default=0.00) 
#     other_charge = models.FloatField(default=0.00)
#     is_service_bill = models.BooleanField(default=False)
#     is_reverse_charge = models.BooleanField(default=False)
#     igst_amount = models.FloatField(default=0.00)
#     cgst_amount = models.FloatField(default=0.00)
#     sgst_amount = models.FloatField(default=0.00)
#     is_expense = models.BooleanField(default=False)
    
#     class Meta:
#         indexes = [
#             models.Index(fields=['company'], name='idx_bill_company'),
#             models.Index(fields=['bill_id'], name='idx_bill_bill_id'),
#         ]

#     def __str__(self):
#         return self.reference_id
    
#     def clean(self):
#         if BillModel.objects.exclude(pk=self.pk).filter(reference=self.reference).exists():
#             raise ValidationError("Reference must be unique.")
#         if BillModel.objects.exclude(pk=self.pk).filter(reference_note=self.reference_note).exists():
#             raise ValidationError("Reference note must be unique.")

   
# class BillInvoiceLineModel(models.Model):
#     bill = models.ForeignKey(
#         BillModel, on_delete=models.CASCADE, blank=True, null=True , related_name="bill_reference")
#     product = models.ForeignKey(
#         ProductModel, on_delete=models.CASCADE, verbose_name="Product", blank=True, null=True) 
#     label = models.TextField(blank=True, null=True)
#     quantity = models.FloatField(default=1.0000, verbose_name="Quantity")
#     unit_price = models.FloatField(default=0.00, verbose_name="Unit Price")
#     description = models.TextField(blank=True, null=True)
#     total = models.FloatField(default=0.00, blank=True,null=True, verbose_name="Sub Total")
#     untax_amount = models.FloatField(default=0.00)
#     tax_amount = models.FloatField(default=0.00)

#     @property
#     def bill_amount(self):
#         total = self.unit_price * self. quantity
#         untaxed_amount = 0.0
#         tax_amount = 0.0 
#         if self.taxes:                     
#             if self.taxes.include == True:
#                 # tax_amount =(item.total*item.product_taxes.amount) / 100
#                 untaxed_amount = (float(total)*100) / (100 + self.taxes.amount)
#                 # untaxed_amount_total = untaxed_amount * float(item.get("quantity")) if item.get("quantity") else 0.0 
#                 tax_amount = float(total) - untaxed_amount
#             else:
#                 untaxed_amount = total
#                 tax_amount =(total*self.taxes.amount) / 100
#         else:
#             untaxed_amount = total
        
#         return {"untax_amount":round(untaxed_amount, 2), "tax_amount":round(tax_amount, 2), "total_amount":round(untaxed_amount+tax_amount, 2)}

#     def save(self, *args, **kwargs):
#         self.untax_amount = self.bill_amount["untax_amount"]
#         self.tax_amount = self.bill_amount["tax_amount"]
#         super(BillInvoiceLineModel, self).save(*args, **kwargs)
