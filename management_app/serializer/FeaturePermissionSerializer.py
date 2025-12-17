from rest_framework import serializers
from user_app.serializers import *
from ..models import *



class FeatureSerializer(serializers.ModelSerializer):

    class Meta:
       model = FeatureModel
       fields = '__all__'

class FeatureApplicationSerializer(serializers.ModelSerializer):
    feature_module = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    def get_feature_module(self,obj):
        if obj.feature:
            return obj.feature.name
        return ''
    
    def get_children(self,obj):
        list = []
        if obj.feature and obj.feature.get_children():
          for ch in obj.feature.get_children().all():
            feature_permission  = FeatureApplication.objects.filter(feature=ch,role=obj.role).first() 
            serializer = FeatureApplicationSerializer(feature_permission)
            list.append(serializer.data)
          return list
        return list

    
    def get_path(self,obj):
        if obj.feature:
            return obj.feature.full_path
        return ''

    class Meta:
       model = FeatureApplication
       fields = '__all__'