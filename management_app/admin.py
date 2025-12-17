from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import *
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from django.utils.html import format_html
# Register your models here.


@admin.register(CategoryTagsModel)
class CategoryTagsAdmin(admin.ModelAdmin,):
    list_display = ("name",)
    search_fields = ("name",)



class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(CategoryModel)
    list_display = ("name", "sequence", "is_active", "category_tags", "full_pathtext")
    list_filter = ("is_active", "category_tags")
    search_fields = ("name", "full_pathtext")
    ordering = ("sequence",)
    

admin.site.register(CategoryModel,CategoryAdmin)

@admin.register(HomeCategoryModel)
class HomeCategoryModelAdmin(ImportExportModelAdmin):
    list_display = ('id','name')
    search_fields = ('id','name')

@admin.register(BrandModel)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id","name", "number","description")
    search_fields = ("name",)


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImageModel
    extra = 1
    readonly_fields = ['image_preview']
    fields = ['image','image_preview']

    def image_preview(self,obj):
        if obj.image:
             return format_html('<img src="{}" width="100" height="75" style="object-fit:cover; border-radius:4px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'

@admin.register(ProductImageModel)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['id','product', 'image']
    readonly_fields = ['thumbnail_preview']
    
    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="75" style="object-fit:cover; border-radius:4px;" />', obj.image.url)
        return "-"
    thumbnail_preview.short_description = 'Preview'

from django.template.loader import get_template

@admin.register(ProductModel)
class ProductAdmin(ImportExportModelAdmin):
    list_display = ("id","name","item_code", "short_name","company", "product_price", "is_published", "is_archived")
    list_filter = ("brand", "category","sub_category", "is_published", "is_archived","home_categories")
    search_fields = ("name", "short_name", "item_code", "company_code", "hsn_code", "upc_barcode", "lan_barcode","company__name")
    inlines = (ProductImageInline,)
    ordering = ("-created_at",)
    filter_horizontal = ("product_tag","category","sub_category",'home_categories')
    readonly_fields = ("updated_at",)
    fieldsets = (
        ("Basic Info", {
            "fields": (
                "image_inline", "name", "item_code", "short_name", "brand","company", "category", "sub_category", 'home_categories', 
                "product_type", "product_use_type", "unit"
            )
        }),
        ("Pricing & Tax", {
            "fields": (
                "product_price", "retailer_price", "distributer_price", 
                "super_distributer_price", "cost", "gst", "sales_discount"
            )
        }),
        ("Stock & Sales", {
            "fields": (
                "limited_stock", "out_of_stock", "warranty", "weight", 
                "can_be_sold", "can_be_purchased", "is_tracking"
            )
        }),
        ("Codes & Barcodes", {
            "fields": (
                "company_code", "hsn_code", 
                "upc_barcode", "lan_barcode", "barcode_image"
            )
        }),
        ("Media", {
            # "classes": ("collapse",),  # collapsible in admin
            "fields": ( "video_link", "web_link") # "image1", "image2", "image3", "image4", "image5",
        }),
        ("Extra Info", {
            # "classes": ("collapse",),
            "fields": ("description","short_description","group", "model", "color", "feature",  "notes", "document")
        }),
        ("Status & Flags", {
            "fields": (
                "is_active", "is_published", "is_archived", "is_favourite"
            )
        }),
        ("System", {
            # "classes": ("collapse",),
            "fields": ("created_at", "updated_at", "deleted_at")
        }),
    )
    readonly_fields= ('image_inline',"created_at", "updated_at", "deleted_at")
    
    def image_inline(self, *args, **kwargs):
        context = getattr(self.response, 'context_data', None) or {}
        inline = context['inline_admin_formset'] = context['inline_admin_formsets'].pop(0)
        return get_template(inline.opts.template).render(context, self.request)

    def render_change_form(self, request, *args, **kwargs):
        self.request = request
        self.response = super().render_change_form(request, *args, **kwargs)
        return self.response


@admin.register(NewsModel)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "role")
    search_fields = ("title",)
    list_filter = ("role",)


@admin.register(BusinessCategoryModel)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(InquiryModel)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "status")
    list_filter = ("status",)
    search_fields = ("name__email",)


@admin.register(FeedbackModel)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id","title", "email","description")
    search_fields = ("title", "email")


@admin.register(HelpAndSupportModel)
class HelpAndSupportAdmin(admin.ModelAdmin):
    list_display = ("title", "email")
    search_fields = ("title", "email")


@admin.register(FirmModel)
class FirmAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("name", "user__email")


@admin.register(ThirdPartyModel)
class ThirdPartyAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("name", "user__email")


class OrderLinesInline(admin.TabularInline):
    model = OrderLinesModel
    extra = 1


@admin.register(OrderModel)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "customer", "order_status", "final_total", "is_paid", "created_at","order_date")
    list_filter = ("order_id","order_status", "is_paid", "is_expired", "is_gift", "is_ecommerce")
    search_fields = ("order_id", "customer__email","order_number")
    ordering = ("-created_at",)
    inlines = [OrderLinesInline]


@admin.register(OrderLinesModel)
class OrderLinesAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "selling_price", "product_total")
    search_fields = ("order__order_id", "product__name")


@admin.register(LocationModel)
class LocationModelAdmin(admin.ModelAdmin):
    list_display = (
        "id", "location_name", "location_type", "parent_location",
        "is_a_scrap_location", "is_a_return_location", "barcode"
    )
    list_filter = ("location_type", "is_a_scrap_location", "is_a_return_location")
    search_fields = ("location_name", "barcode")
    ordering = ("location_name",)


@admin.register(SerialNumbersModel)
class SerialNumbersModelAdmin(admin.ModelAdmin):
    list_display = (
        "id", "serial_no", "product", "created_on",
        "best_before_date", "removal_date", "end_of_life",
        "alert_time", "is_repacked"
    )
    list_filter = ("is_repacked", "created_on", "best_before_date", "removal_date")
    search_fields = ("serial_no", "product__name")
    ordering = ("-created_on",)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "id", "product", "location_stock",
        "formatted_quantity", "formatted_counted_quantity",
        "formatted_reserved_quantity", "value","created_at","last_updated"
    )
    list_filter = ("created_at", "location_stock", "product")
    search_fields = ("product__name", "location_stock__location_name")
    ordering = ("-created_at",)
    readonly_fields = ("value", "difference")
    autocomplete_fields = ["product"]


@admin.register(KYCDetailsModel)
class KYCDetailsAdmin(admin.ModelAdmin):
    list_display = ("firm_name", "business_category", "gstin_no", "pancard_no", "sez_company", "csc_funding_company")
    search_fields = ("firm_name", "gstin_no", "pancard_no", "cin_no")
    list_filter = ("business_category", "sez_company", "csc_funding_company")


@admin.register(BankDetailsModel)
class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ("bank_name", "account_number", "ifsc_code", "account_holder_name", "kyc_detail")
    search_fields = ("bank_name", "account_number", "ifsc_code")
    list_filter = ("bank_name",)


@admin.register(VersionModel)
class VersionAdmin(admin.ModelAdmin):
    list_display = ("android_id","android_version","android_description","android_status","ios_id",
                    "ios_version","ios_description","ios_status")
    search_fields = ("android_id","ios_id")


@admin.register(FavouriteModel)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ("user_id", "product_id", "status", "created_at", "updated_at", "deleted_at")
    search_fields = ("user_id", "product_id", "created_at")
    
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
            "id","user","product","brand","qty","price","total_price","status","created_at","updated_at",
        )
    list_filter = ("status", "created_at", "updated_at", "brand")
    search_fields = ("user__email", "user__first_name", "user__last_name", "product__name", "brand__name")
    ordering = ("-created_at",)

    def total_price(self, obj):
            return obj.total_price
        
@admin.register(OnlinePaymentOffer)
class OnlinePaymentOfferAdmin(admin.ModelAdmin):
    list_display = ('start_price_value','end_price_value','percentage_off')
    

@admin.register(PageModel)
class PageModelAdmin(ImportExportModelAdmin):
    list_display = ('id','title','type')
    list_filter =('title', 'type')
    ordering = ('-created_at',)


@admin.register(OfferModel)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "roles", "description")
    search_fields = ("title", "roles")
    list_filter = ("roles",)
    ordering = ("-id",)


@admin.register(OnlinePaymentOfferModel)
class OnlinePaymentOfferAdmin(admin.ModelAdmin):
    list_display = ("id", "start_price", "end_price", "percentage_off")
    search_fields = ("start_price", "end_price")
    ordering = ("start_price",)


@admin.register(OfferSliderModel)
class OfferSliderAdmin(admin.ModelAdmin):
    list_display = ("id", "banner_number","created_at","updated_at")
    ordering = ("banner_number",)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1  # show at least one empty row
    readonly_fields = ("total_price",)
    autocomplete_fields = ["product"]

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "email", "phone", "payment_terms")
    search_fields = ("name", "contact_person", "email", "phone")
    list_filter = ("payment_terms",)

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "order_date", "expected_delivery", "order_status")
    list_filter = ("status", "order_date", "vendor")
    search_fields = ("vendor__name",)
    date_hierarchy = "order_date"
    inlines = [PurchaseOrderItemInline]

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ("id","purchase_order", "product", "quantity", "unit_price", "total_price")
    list_filter = ("purchase_order__status",)
    search_fields = ("product__name", "purchase_order__id")
    
@admin.register(CompanyModel)
class CompanyModelAdmin(admin.ModelAdmin):
    list_display = ('id','name','code','email','phone_no','gstin')
    list_filter = ("address__address", "code")
    search_fields = ('name','code')


@admin.register(ProductReviewModel)
class ProductReviewModelAdmin(ImportExportModelAdmin):
    list_display = ("published_at", "review", "rating",
                    "product", "id", "user")[::-1]
    autocomplete_fields = ["product"]
 
@admin.register(BlogModel)
class BlogModelAdmin(ImportExportModelAdmin):
    list_display = ("published_at",
                    "is_published", "banner", "title", "id")[::-1]
    
    search_fields = ['title']


@admin.register(OnlinePaymentsModel)
class OnlinePaymentsAdmin(admin.ModelAdmin):
    list_display = ('txn_id', 'order_id', 'user', 'amount', 'status', 'payment_datetime')
    list_filter = ('status', 'payment_datetime')
    search_fields = ('txn_id', 'order_id__id', 'user__name')  # Assuming ContactModel has 'name'
    ordering = ('-payment_datetime',)


@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
from django.contrib import admin
from .models import ContactModel


@admin.register(ContactModel)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "contact_type",
        "contact_role",
        "phone_no",
        "email",
        "country",
        "is_active",
        "created_at",
    )
    list_filter = (
        "contact_type",
        "contact_role",
        "is_active",
        "country",
        "mail_subscription_status",
        "created_at",
    )
    search_fields = (
        "name",
        "phone_no",
        "another_phone_no",
        "email",
        "gstin",
        "pan_number",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user", "address", "country")
    filter_horizontal = ("many_address",)  # for ManyToManyField
    ordering = ("-created_at",)
    fieldsets = (
        ("Basic Information", {
            "fields": (
                "user",
                "contact_type",
                "contact_role",
                "name",
                "is_active",
                "created_at",
            )
        }),
        ("Contact Details", {
            "fields": (
                "phone_no",
                "another_phone_no",
                "email",
                "website",
            )
        }),
        ("Address", {
            "fields": (
                "address",
                "many_address",
                "country",
            )
        }),
        ("Legal Info", {
            "fields": (
                "gstin",
                "pan_number",
            )
        }),
        ("Preferences", {
            "fields": (
                "mail_subscription_status",
            )
        }),
    )


class FeatureModelAdmin(TreeAdmin,ImportExportModelAdmin):
    form = movenodeform_factory(FeatureModel)
    list_display = ("id",'name' , 'full_path','component','icon')       
    search_fields = ('id','name')  

admin.site.register(FeatureModel,FeatureModelAdmin)           

@admin.register(FeatureApplication)
class FeatureApplicationModelAdmin(ImportExportModelAdmin):
    list_display = ("id" , "role","feature","is_viewed","is_read","is_write","is_delete",'sequence_no')
    autocomplete_fields = ["feature"]
    search_fields = ('role__name','role__type')


# @admin.register(BillModel)
# class BillModelAdmin(ImportExportModelAdmin):
#     list_display = ('id','company', 'created_by','bill_id', "reference", 'bill_date', 'vendor','source_doc', 'is_post')
#     search_fields = ('bill_id',)

# @admin.register(BillInvoiceLineModel)
# class BillInvoiceLineModelAdmin(ImportExportModelAdmin):
#     list_display = ("total", "description",
#                     "unit_price","quantity", "label", "product", "bill", "bill_amount","tax_amount","untax_amount", "id")[::-1]
#     search_fields = ('bill__bill_id', "id")

@admin.register(CategoryTranslation)
class CatyegoryTranslationModelAdmin(admin.ModelAdmin):
    list_display = ('id','category', 'language_code', 'name')
    search_fields = ('category__name', 'language_code', 'name')
@admin.register(ProductTranslation)
class ProductTranslationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'language_code', 'name', 'short_name', 'feature')
    search_fields = ('product__name', 'language_code', 'name', 'short_name', 'feature')
    list_filter = ('language_code',)
    
@admin.register(HomeCategoryTranslation)
class HomeCategoryTranslationModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'home_category', 'language_code', 'name')
    search_fields = ('home_category__name', 'language_code', 'name')
    list_filter = ('language_code',)
    ordering = ('home_category__name',)

@admin.register(PageTranslation)
class PageTranslationModelAdmin(ImportExportModelAdmin):
    list_display = ('id','title','language_code')
    search_fields = ('title', 'language_code', 'description')
    ordering = ('-id',)
    
@admin.register(ClientTranslation)
class ClientTranslationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'language_code', 'name')
    search_fields = ('client__name', 'language_code', 'name')
