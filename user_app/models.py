from django.db import models
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, Group, PermissionsMixin)
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from uuid import uuid4
from rest_framework.authtoken.models import Token

# Create your models here.
class AccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        values = [email]
        field_value_map = dict(zip(self.model.REQUIRED_FIELDS, values))
        for field_name, value in field_value_map.items():
            if not value:
                raise ValueError("The {} value must be set".format(field_name))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        Token.objects.create(user=user)
        
        if extra_fields['is_superuser']:
            adminGroup, _ = Group.objects.get_or_create(name='Admin')
            adminGroup.user_set.add(user)
            
        return user
    

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", RoleModel.objects.get(type='Admin'))

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
    

class RoleModel(models.Model):
    name = models.CharField(max_length=150)
    type = models.CharField(choices=[('Admin','Admin'),('Retailer','Retailer'),('Wholesaler','Wholesaler'),('Distributer','Distributer'),('Employee','Employee')],max_length=100,null=True,blank=True)

    def __str__(self):
        return self.type
    
    class Meta:
        indexes = [
            models.Index(fields=['name'], name='idx_role_name'),
            models.Index(fields=['type'], name='idx_role_type'),
        ]

class CountryModel(models.Model):
    country_name = models.CharField(
        verbose_name='name', max_length=255, unique=True)
    country_code = models.CharField(verbose_name='country code', max_length=3)
    currency = models.CharField(max_length=3)
    calling_code = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'country'
        verbose_name_plural = 'countries'

    def __str__(self):
        return self.country_name

class CountryGroupModel(models.Model):
    group_name = models.CharField(max_length=255, verbose_name="group name")
    countries = models.ManyToManyField(CountryModel)

    class Meta:
        verbose_name = 'country group'
        verbose_name_plural = 'country groups'


class StatesModel(models.Model):
    country = models.ForeignKey(CountryModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CitiesModel(models.Model):
    country = models.ForeignKey(CountryModel, on_delete=models.CASCADE)
    state = models.ForeignKey(StatesModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AddressModel(models.Model):
    address_types = (('Office', 'Office'),
                     ('Home', 'Home'), ('Other', 'Other'))
    full_name = models.CharField(max_length=255, blank=True, null=True)
    address_tags = models.CharField(
        choices=address_types, max_length=255, blank=True, null=True)
    mobile = PhoneNumberField(blank=True, null=True)
    another_mobile = PhoneNumberField(blank=True, null=True)
    street = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10, verbose_name='pin code', blank=True, null=True)
    fcity = models.ForeignKey(CitiesModel, on_delete=models.SET_NULL, blank=True, null=True)
    fstate = models.ForeignKey(StatesModel, on_delete=models.SET_NULL, blank=True, null=True)
    fcountry = models.ForeignKey(CountryModel, on_delete=models.SET_NULL, blank=True, null=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    state = models.CharField(max_length=150, blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)
    postal_code = models.CharField(max_length=10, verbose_name='postal code', blank=True, null=True)

    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'address'
        verbose_name_plural = 'addresses'

    def __str__(self):
        return f"{self.address}, {self.landmark if self.landmark else ''}, {self.city if self.city else ''}, {self.state if self.state else ''}, {self.country if self.country else ''} - {self.pincode if self.pincode else self.postal_code if self.postal_code else ''}"


class UserModel(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    role = models.ForeignKey(RoleModel,on_delete=models.CASCADE,null=True,blank=True)
    mobile_no = PhoneNumberField(null=True,blank=True)
    address = models.ManyToManyField(AddressModel, blank=True)
    firm_name = models.CharField(max_length=100,blank=True,null=True)
    token = models.CharField(max_length=255,blank=True,null=True)
    approved_status = models.CharField(max_length=100,null=True,blank=True,choices=[('Pending','Pending'),('Approved','Approved')])
    unpaid_amount = models.FloatField(default=0.00)
    advance_amount = models.FloatField(default=0.00)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    
    def usergroups(self):
        return "".join([l.name for l in self.groups.all()])

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

class ProfileModel(models.Model):
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='Profile', blank=True, null=True)
    mobile_no = PhoneNumberField(unique=True, blank=True, null=True)
    addresses = models.ManyToManyField(AddressModel, blank=True)
    otp = models.IntegerField(blank=True, null=True)
    otp_requested_at = models.DateTimeField(blank=True, null=True)
    os_type = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.email
    
    class Meta:
        indexes = [
            models.Index(fields=['user'], name='idx_profile_user'),
            models.Index(fields=['mobile_no'], name='idx_profile_mobile_no_unique'),
        ]


class PasswordResetLinkModel(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    reset_uuid = models.CharField(default=uuid4, editable=False ,max_length = 255)
    url_link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.reset_uuid

class VisitorModel(models.Model):
    visitor_id = models.CharField(max_length=255)

    def __str__(self):
        return self.visitor_id

    class Meta:
        indexes = [
            models.Index(fields=['visitor_id'], name='idx_visitor_id'),
        ]    
        verbose_name = 'visitor'
        verbose_name_plural = 'visitors'
        
        
    
class ContactUsModel(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=255)  
    message = models.TextField()
    
    class Meta:
        verbose_name = 'contact us'
        verbose_name_plural = 'contact us entries'
        
        
DEVICE_CHOICES = (
    ('android', 'android'),
    ('ios', 'ios'),
    ('web', 'web'),
    ('desktop', 'desktop'),
    ('other', 'other'),
)

class FCMTokenModel(models.Model):
    device_type = models.CharField(max_length=10, choices=DEVICE_CHOICES, default='android')
    user_id = models.CharField(max_length=10, verbose_name='User ID')
    token = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255, default='Unknown Device')
    created_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user_id} - {self.device_type} - {self.token[:10]}..."


class Notification(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    user_id = models.CharField(max_length=255, blank=True, null=True)
    customer_id = models.CharField(max_length=255)
    image_url = models.URLField(null=True, blank=True)  # 📷 Optional image
    video_url = models.URLField(null=True, blank=True)  # 📺 Optional video
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    