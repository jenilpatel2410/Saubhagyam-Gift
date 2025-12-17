from rest_framework import serializers
from ..models import PageModel


class PageModelSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H-%M-%S')
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H-%M-%S')
    deleted_at = serializers. DateTimeField(format='%Y-%m-%d %H-%M-%S')
    
    class Meta:
        model = PageModel
        fields = ['id', 'description', 'type', 'created_at', 'updated_at', 'deleted_at']
        
    def get_description(self, obj):
        # Get language from serializer context
        lang = self.context.get('lang', 'en')

        if lang == 'en':
            return obj.description

        # Assuming you have a related translations table like `PageTranslation`
        translation = obj.translations.filter(language_code=lang).first()
        if translation:
            return translation.description
        return obj.description  # fallback to English
