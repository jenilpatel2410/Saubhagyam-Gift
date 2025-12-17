from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
# Register your models here.

class UserAdmin(BaseUserAdmin):
    model = UserModel
    list_display = ("id","mobile_no","email", "first_name", "last_name", "role", "is_active", "is_staff","advance_amount","unpaid_amount")
    list_filter = ("is_active", "is_staff", "is_superuser", "role")
    search_fields = ("email", "first_name", "last_name", "mobile_no")
    ordering = ("-id",)
    filter_horizontal = ("address",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "mobile_no", "address","firm_name","token")}),
        ("Role & Status", {"fields": ("role", "approved_status","advance_amount","unpaid_amount")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2", "role", "is_active", "is_staff"),
        }),
    )
    
@admin.register(ProfileModel)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "mobile_no", "otp", "otp_requested_at")
    search_fields = ("user__email", "mobile_no")
    list_filter = ("otp_requested_at",)


@admin.register(RoleModel)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id","name","type")
    search_fields = ("name",)


@admin.register(CountryModel)
class CountryAdmin(ImportExportModelAdmin):
    list_display = ("country_name", "country_code", "currency", "calling_code")
    search_fields = ("country_name", "country_code")


@admin.register(CountryGroupModel)
class CountryGroupAdmin(admin.ModelAdmin):
    list_display = ("group_name",)
    filter_horizontal = ("countries",)


@admin.register(StatesModel)
class StatesAdmin(ImportExportModelAdmin):
    list_display = ("name", "country")
    search_fields = ("name",)
    list_filter = ("country",)


@admin.register(CitiesModel)
class CitiesAdmin(ImportExportModelAdmin):
    list_display = ("name", "state", "country", "is_active")
    list_filter = ("is_active", "country", "state")
    search_fields = ("name",)


@admin.register(AddressModel)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id","full_name", "address_tags", "city", "state", "country","pincode", "is_default")
    search_fields = ("full_name", "street", "address", "landmark")
    list_filter = ("is_default", "country", "state", "city")


# Finally register UserModel with custom admin
admin.site.register(UserModel, UserAdmin)

@admin.register(VisitorModel)
class VisitorModelAdmin(ImportExportModelAdmin):
    list_display = ("visitor_id", "id")
    list_per_page = 2500
    search_fields = ["visitor_id"]
    
@admin.register(PasswordResetLinkModel)
class PasswordResetLinkModelAdmin(ImportExportModelAdmin):
    list_display = ("updated_at", "created_at",
                    "url_link", "reset_uuid", "user")
    
    
@admin.register(ContactUsModel)
class ContactUsModelAdmin(ImportExportModelAdmin):
    list_display = ("id", "name", "email", "mobile_no", "subject", "message")
    search_fields = ("name", "email", "mobile_no", "subject", "message")    
    

@admin.register(FCMTokenModel)
class FCMTokenModelAdmin(ImportExportModelAdmin):
    list_display = ("user_id", "token")

@admin.register(Notification)
class NotificationAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "body", "created_at", "customer_id", "user_id")
    search_fields = ("title", "body")
    list_filter = ("created_at",)