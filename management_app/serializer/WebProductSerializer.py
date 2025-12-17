from rest_framework import serializers
from management_app.models import ProductModel , ProductReviewModel,Cart,CategoryTranslation
from user_app.models import VisitorModel
from django.db import models
from django.utils.text import slugify
from django.db.models import Count, Case, When, IntegerField
from management_app.serializer.ProductSerializer import ProductImageSerializer
import os


class WebProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField(read_only=True)
    product_tag_list = serializers.SerializerMethodField(read_only=True)
    product_price = serializers.SerializerMethodField(read_only=True)
    # category_slug = serializers.SerializerMethodField(read_only=True)
    # sub_category_slug = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.SerializerMethodField()
    parent_category_name = serializers.SerializerMethodField()
    base_price = serializers.FloatField(source='product_price')
    discount_price = serializers.FloatField(source='product_price')
    discount = serializers.FloatField(default=0)
    product_images = ProductImageSerializer(many=True, source='images')
    image1 = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    
    # def get_name(self, obj):
    #     return obj.name.title()
    def get_name(self, obj):
        lang = self.context.get('lang', 'en')
        # Try to get translation for the product
        translation = getattr(obj, "translations", None)
        if translation and translation.filter(language_code=lang).exists():
            return translation.filter(language_code=lang).first().name
        return obj.name.title()
    
    def get_product_price(self, obj):
        request = self.context.get("request")
        if not obj:
            return 0.0

        if request and getattr(request, "user", None) and getattr(request.user, "role", None):
            role_type = request.user.role.type

            if role_type == "Retailer" and obj.retailer_price:
                return float(obj.retailer_price)
            elif role_type == "Wholesaler" and obj.distributer_price:
                return float(obj.distributer_price)
            elif role_type == "Distributer" and obj.distributer_price:
                return float(obj.distributer_price)
            else:
                return float(obj.product_price)
        else:
            return float(obj.product_price)

    def get_average_rating(self, obj):
        get_product_review_rating = ProductReviewModel.objects.filter(product=obj).select_related('user').order_by('published_at')
        
        avg_rating = get_product_review_rating.aggregate(avg_rating=models.Avg('rating'))['avg_rating']

        return {"average_rating": round(avg_rating, 1) if avg_rating else 0.0, 'review_count': get_product_review_rating.count()}


    def get_product_tag_list(self, obj):
        if obj.product_tag:
            return [i.name for i in obj.product_tag.all()]
        else:
            return []
    
    # def get_category_slug(self,obj):
    #     if obj.category:
    #        return slugify(obj.category.get_parent().name) 
    #     return ""
        
    # def get_sub_category_slug(self,obj):
        
    #     if obj.category:
    #         if obj.category.name == 'Raksha Bandhan':
    #             return f"{obj.category.name.lower().replace(' ','')}"
    #         else:
    #             return f"{obj.category.name.lower().replace(' ','-')}"

    # def get_category_name(self, obj):
    #     if obj.category:
    #         return slugify(obj.category.name)
    #     return None

    # def get_parent_category_name(self, obj):
    #     if obj.category:
    #         ancestors = obj.category.get_ancestors()
    #         if ancestors.exists():
    #             return slugify(ancestors.first().name)  # only first ancestor
    #     return None
    
    # def get_category_name(self, obj):
    #     sub_categories = obj.sub_category.all()
    #     return [slugify(cat.name) for cat in sub_categories] if sub_categories.exists() else None

    # def get_parent_category_name(self, obj):
    #     categories = obj.category.all()
    #     return [slugify(cat.name) for cat in categories] if categories.exists() else None
    
    def get_category_name(self, obj):
        lang = self.context.get('lang', 'en')
        names = []

        # Case 1: If product has ManyToMany category field
        if hasattr(obj, 'sub_category') and hasattr(obj.sub_category, 'all'):
            for cat in obj.sub_category.all():
                translation = CategoryTranslation.objects.filter(category=cat, language_code=lang).first()
                names.append(translation.name if translation else cat.name)

        # Case 2: If product has ForeignKey category field
        elif hasattr(obj, 'sub_category') and obj.sub_category:
            cat = obj.sub_category
            translation = CategoryTranslation.objects.filter(category=cat, language_code=lang).first()
            names.append(translation.name if translation else cat.name)

        return names or None

    def get_parent_category_name(self, obj):
        lang = self.context.get('lang', 'en')
        names = []

        # For each category, get its parent if it exists
        if hasattr(obj, 'category') and hasattr(obj.category, 'all'):
            for cat in obj.category.all():
                translation = CategoryTranslation.objects.filter(category=cat, language_code=lang).first()
                names.append(translation.name if translation else cat.name)

        elif hasattr(obj, 'category') and obj.category:
            cat = obj.category
            translation = CategoryTranslation.objects.filter(category=cat, language_code=lang).first()
            names.append(translation.name if translation else cat.name)

        return names or None
    
    def get_image1(self, obj):
        first_image = obj.images.first()  # assuming reverse relation name is 'images'
        if first_image and hasattr(first_image, "image") and first_image.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None

    class Meta:
        model = ProductModel
        fields = ('id', 'encrypted_id', 'name', 'category','image1', 'base_price', 'discount_price', 'discount', 'brand', 'is_published','is_archived' , 'average_rating', 'product_tag_list', "product_price", 'category_name', 'parent_category_name','product_images')
        read_only_fields = fields




class ProductDetailSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField(read_only=True)
    product_tag_list = serializers.SerializerMethodField(read_only=True)
    images = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    rating_review_data = serializers.SerializerMethodField(read_only=True)
    is_add_to_cart = serializers.SerializerMethodField(read_only=True)
    related_products = serializers.SerializerMethodField(read_only=True)
    product_price = serializers.SerializerMethodField(read_only=True)
    base_price = serializers.FloatField(source='product_price')
    discount_price = serializers.FloatField(source='product_price')
    discount = serializers.FloatField(default=0)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    parent_category_name = serializers.SerializerMethodField()
    
    def get_product_price(self, obj):
        request = self.context.get("request") 
        if not obj:
            return 0.0

        if request and getattr(request, "user", None) and getattr(request.user, "role", None):
            role_type = request.user.role.type

            if role_type == "Retailer" and obj.retailer_price:
                return float(obj.retailer_price)
            elif role_type == "Wholesaler" and obj.distributer_price:
                return float(obj.distributer_price)
            elif role_type == "Distributer" and obj.distributer_price:
                return float(obj.distributer_price)
            else:
                return float(obj.product_price)
        else:
            return float(obj.product_price)
    
    def get_average_rating(self, obj):
        get_product_review_rating = ProductReviewModel.objects.filter(product=obj).select_related('user').order_by('published_at')
        
        all_reviews = ProductReviewModel.objects.filter(product=obj)
        star_distribution = all_reviews.aggregate(
            star_5=Count(Case(When(rating=5, then=1), output_field=IntegerField())),
            star_4=Count(Case(When(rating=4, then=1), output_field=IntegerField())),
            star_3=Count(Case(When(rating=3, then=1), output_field=IntegerField())),
            star_2=Count(Case(When(rating=2, then=1), output_field=IntegerField())),
            star_1=Count(Case(When(rating=1, then=1), output_field=IntegerField())),
        )
        
        avg_rating = get_product_review_rating.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
        
        return {
            "star_distribution": {
                5: star_distribution['star_5'],
                4: star_distribution['star_4'],
                3: star_distribution['star_3'],
                2: star_distribution['star_2'],
                1: star_distribution['star_1']
            },
            "average_rating": round(avg_rating, 1) if avg_rating else 0.0, 
            'review_count': get_product_review_rating.count()
            }
    
    # def get_product_tag_list(self, obj):
    #     if obj.product_tag:
    #         return [i.name for i in obj.product_tag.all()]
    #     else:
    #         return []
    def get_name(self, obj):
        lang = self.context.get('lang', 'en')
        translation = getattr(obj, 'translations', None)
        if translation and translation.filter(language_code=lang).exists():
            return translation.filter(language_code=lang).first().name
        return obj.name

    def get_description(self, obj):
        lang = self.context.get('lang', 'en')
        translation = getattr(obj, 'translations', None)
        if translation and translation.filter(language_code=lang).exists():
            return translation.filter(language_code=lang).first().description
        return obj.description

    def get_product_tag_list(self, obj):
        lang = self.context.get('lang', 'en')
        if obj.product_tag.exists():
            tags = []
            for tag in obj.product_tag.all():
                translation = getattr(tag, 'translations', None)
                if translation and translation.filter(language_code=lang).exists():
                    tags.append(translation.filter(language_code=lang).first().name)
                else:
                    tags.append(tag.name)
            return tags
        return []

    def get_category_name(self, obj):
        lang = self.context.get('lang', 'en')
        names = []
        for cat in obj.sub_category.all() if hasattr(obj, 'sub_category') else []:
            translation = CategoryTranslation.objects.filter(category=cat, language_code=lang).first()
            names.append(translation.name if translation else cat.name)
        return names or None

    def get_parent_category_name(self, obj):
        lang = self.context.get('lang', 'en')
        names = []
        for cat in obj.category.all() if hasattr(obj, 'category') else []:
            translation = CategoryTranslation.objects.filter(category=cat, language_code=lang).first()
            names.append(translation.name if translation else cat.name)
        return names or None

    # def get_images(self, obj):
    #     request = self.context['request']

    #     product_images = []
    #     for _ in ProductModel.objects.filter(id=obj.id):
    #         product_images.append(str(request.build_absolute_uri(
    #             obj.image1.url))) if obj.image1 else None
    #         product_images.append(str(request.build_absolute_uri(
    #             obj.image2.url))) if obj.image2 else None
    #         product_images.append(str(request.build_absolute_uri(
    #             obj.image3.url))) if obj.image3 else None
    #         product_images.append(str(request.build_absolute_uri(
    #             obj.image4.url))) if obj.image4 else None
    #         product_images.append(str(request.build_absolute_uri(
    #             obj.image5.url))) if obj.image5 else None

    #     # product_videos = obj.product_videos.all()
    #     # for video in product_videos:
    #     #     product_images.append(str(video.video_url))
            
    #     return product_images
    
    def get_images(self, obj):
        request = self.context.get("request")
        data = []
        for media in obj.images.all():
            if request and media.image:
                ext = os.path.splitext(media.image.name)[1].lower()
                if ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
                    media_type = "video"
                else:
                    media_type = "image"

                data.append(
                    {
                        "id": media.id,
                        "type": media_type,
                        "src": request.build_absolute_uri(media.image.url)
                    }
                )
        return data


    def get_rating_review_data(self, obj):  # Method to fetch review data
        reviews = ProductReviewModel.objects.filter(product=obj).select_related('user').order_by('-published_at')[:3]
        return [
            {
                'name': f"{review.user.first_name} {review.user.last_name}" if review.user else 'Anonymous',
                'rating': review.rating,
                'review': review.review,
                'published_at': review.published_at
            }
            for review in reviews
        ]
        
    def get_is_add_to_cart(self, obj):
        request = self.context.get("request")

        if not request:
            return False

        visitor_id = request.headers['Visitor'] if "Visitor" in request.headers.keys() else None
        get_user_token = request.headers['Authorization'].split()[-1] if "Authorization" in request.headers.keys() else None

        if get_user_token is not None and request.user.is_authenticated:
            return Cart.objects.filter(user__id=request.user.id, product=obj).exists()

        elif visitor_id is not None:
            visitor_user = VisitorModel.objects.filter(visitor_id=visitor_id).first()
            if visitor_user:
                return Cart.objects.filter(visitor__id=visitor_user.id, product=obj).exists()

        return False

    # def get_related_products(self, obj):
    #     if obj.category:
    #         # first fetch from same category
    #         products = list(
    #             ProductModel.objects.filter(category=obj.category).exclude(id=obj.id).order_by('-created_at')[:6]
    #         )

    #         # if less than 6 → fill from parent category
    #         if len(products) < 6 and obj.category.get_parent():
    #             needed = 6 - len(products)
    #             sibling_categories = obj.category.get_parent().get_descendants().exclude(id=obj.category.id)

    #             parent_products = (
    #                 ProductModel.objects.filter(category__in=sibling_categories)
    #                 .exclude(id__in=[p.id for p in products] + [obj.id])
    #                 .order_by("-created_at")[:needed]
    #             )

    #             products.extend(parent_products)

    #         serializer = WebProductSerializer(products, many=True)
    #         return serializer.data
    #     return []
    
    def get_related_products(self, obj):
        categories = obj.category.all()
        related_products = []

        if categories.exists():
            for category in categories:
                # fetch from same category
                products = list(
                    ProductModel.objects.filter(category=category)
                    .exclude(id=obj.id)
                    .order_by("-created_at")[:6]
                )

                # if less than 6 → fill from parent category
                if len(products) < 6 and category.get_parent():
                    needed = 6 - len(products)
                    sibling_categories = category.get_parent().get_descendants().exclude(id=category.id)

                    parent_products = (
                        ProductModel.objects.filter(category__in=sibling_categories)
                        .exclude(id__in=[p.id for p in products] + [obj.id])
                        .order_by("-created_at")[:needed]
                    )

                    products.extend(parent_products)

                related_products.extend(products)

            # remove duplicates (if product belongs to multiple categories)
            related_products = list({p.id: p for p in related_products}.values())

            # limit to 6
            related_products = related_products[:6]

            lang = self.context.get('lang', 'en')
            serializer = WebProductSerializer(related_products, many=True, context={'request': self.context.get('request'), 'lang': lang})
            return serializer.data
        else :
            products = ProductModel.objects.filter(is_published = True).exclude(id=obj.id).order_by('-id')[:6]
            lang = self.context.get('lang', 'en')
            serializer = WebProductSerializer(products, many=True, context={'request': self.context.get('request'), 'lang': lang})
            return serializer.data      


    class Meta:
        model = ProductModel
        fields = ['id', 'average_rating', 'name', 'base_price', 'discount_price', 'discount', 'product_price','rating_review_data', 'product_tag_list', 'images', 'brand_name', 'description', 'created_at', 'category','category_name','parent_category_name', 'brand', 'home_categories', 'product_tag','is_add_to_cart', 'related_products']
        read_only_fields = fields
