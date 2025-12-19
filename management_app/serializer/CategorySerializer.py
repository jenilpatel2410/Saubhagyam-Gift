from rest_framework import serializers
from ..models import *


class CategorySerializer(serializers.ModelSerializer):
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = CategoryModel
        fields = ('id','name','image','remove_image')

    def update(self, instance, validated_data):
        remove_image = validated_data.pop('remove_image',False)
        if remove_image:
            instance.image.delete(save=False)
            instance.image = None
        return super().update(instance, validated_data)

    def create(self, validated_data):
        validated_data.pop('remove_image')
        return CategoryModel.add_root(**validated_data)

class MobileCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    category_image =serializers.ImageField(source="image")
    class Meta:
        model = CategoryModel
        fields = ('id','category_name','category_image')

    def create(self, validated_data):
        return CategoryModel.add_root(**validated_data)
    
    def get_category_name(self, obj):
        # Get language from context (passed from the view)
        lang = self.context.get('lang', 'en')

        if lang == 'en':
            return obj.name

        translation = obj.translations.filter(language_code=lang).first()
        if translation:
            return translation.name
        return obj.name  # fallback to English


class SubCategorySerializer(serializers.ModelSerializer):
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)
    main_category = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(write_only=True)
   
    def get_main_category(self,obj):
        if obj.get_parent():
            return obj.get_parent().name
        else:
            return ''
    
    def create(self, validated_data):
        parent_id = validated_data.pop('parent_id',None)
        if not parent_id:
            raise serializers.ValidationError({"parent_id": "This field is required."})
        try:
            parent = CategoryModel.objects.get(id=parent_id)
        except CategoryModel.DoesNotExist:
            raise serializers.ValidationError({"parent_id": "Parent category not found."})
        
        validated_data.pop('remove_image',None)
        return parent.add_child(**validated_data)

    def update(self, instance, validated_data):
        parent_id = validated_data.pop('parent_id',None)       
        if  parent_id is not None: 
            try:
                parent = CategoryModel.objects.get(id=parent_id)
                if parent == instance or parent.is_descendant_of(instance):
                      raise serializers.ValidationError({'parent_id': 'Cannot move into self or descendant.'})
            except CategoryModel.DoesNotExist:
                raise serializers.ValidationError({'parent_id': 'Parent category not found.'})
            
            if instance.get_parent() != parent:
                try:
                    if parent.get_last_child() is None:
                            instance.move(parent, 'first-child')
                            instance.refresh_from_db()
                    else:
                            instance.move(parent, 'last-child')
                            instance.refresh_from_db()
                except Exception as e:
                    raise serializers.ValidationError({'move_error': str(e)})
        remove_image = validated_data.pop('remove_image',False)
        if remove_image:
            instance.image.delete(save=False)
            instance.image = None   

        return super().update(instance, validated_data)

    

    class Meta:
        model = CategoryModel

        #Henil
        fields = ('id','name','main_category','image','full_path','parent_id','remove_image')


from rest_framework import serializers
from management_app.models import CategoryModel, CategoryTranslation, BusinessCategoryModel

class MobileSubCategorySerializer(serializers.ModelSerializer):
     
    main_category = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(write_only=True)
    id = serializers.IntegerField(read_only=True)  
    category_id = serializers.IntegerField(source="get_parent.id", read_only=True)
    sub_category_name = serializers.SerializerMethodField()
    sub_category_image = serializers.ImageField(source="image")
    category = serializers.SerializerMethodField()

    def get_lang(self):
        """Fetch lang from serializer context or default to 'en'."""
        return self.context.get('lang', 'en')

    def get_sub_category_name(self, obj):
        lang = self.get_lang()
        if lang != 'en':
            translation = CategoryTranslation.objects.filter(
                category=obj,
                language_code=lang
            ).first()
            if translation:
                return translation.name
        return obj.name

    def get_main_category(self, obj):
        parent = obj.get_parent()
        lang = self.get_lang()
        if parent:
            if lang != 'en':
                translation = CategoryTranslation.objects.filter(
                    category=parent,
                    language_code=lang
                ).first()
                if translation:
                    return translation.name
            return parent.name
        return ''

    def get_category(self, obj):
        """Return translated parent category details (like MobileCategorySerializer but with lang support)."""
        parent = obj.get_parent()
        lang = self.get_lang()
        if parent:
            if lang != 'en':
                translation = CategoryTranslation.objects.filter(
                    category=parent,
                    language_code=lang
                ).first()
                return {
                    "id": parent.id,
                    "category_name": translation.name if translation else parent.name,
                    "category_image": parent.image.url if parent.image else None
                }
            return {
                "id": parent.id,
                "category_name": parent.name,
                "category_image": parent.image.url if parent.image else None
            }
        return None

    class Meta:
        model = CategoryModel
        fields=(
            'id',              
            'category_id',
            'sub_category_name',
            'sub_category_image',
            'main_category',
            'parent_id',
            'category',
        )


class BusinessCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = BusinessCategoryModel
        fields = ['id','name']
