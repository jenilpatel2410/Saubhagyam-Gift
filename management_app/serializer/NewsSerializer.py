from rest_framework import serializers
from ..models import *



class NewsSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.type',default='')

    class Meta:
        model = NewsModel
        fields = ['id','title','image','role','role_name','description']

class MobileNewsModelSerializer(serializers.ModelSerializer):
    news_title = serializers.CharField(source='title')
    news_image = serializers.ImageField(source='image')
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H-%M-%S')
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H-%M-%S')
    deleted_at = serializers.DateTimeField(format='%Y-%m-%d %H-%M-%S')
    class Meta:
        model = NewsModel
        fields = ['id', 'news_title', 'news_image', 'description', 'role_id', 'created_at', 'updated_at', 'deleted_at']
        