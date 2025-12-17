from rest_framework import serializers
from ..models import InquiryModel, ProductModel
from user_app.models import UserModel

class InquirySerializer(serializers.ModelSerializer):
    
    user_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    qty = serializers.IntegerField(source="quantity")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    deleted_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = InquiryModel
        fields = (
            "id",
            "user_id",
            "product_id",
            "qty",
            "description",
            "status",
            "created_at",
            "updated_at",
            "deleted_at",
        )

    def create(self, validated_data):
        user_id = validated_data.pop("user_id")
        product_id = validated_data.pop("product_id")
            
        user = UserModel.objects.get(id=user_id)
        product = ProductModel.objects.get(id=product_id)
        
        inquiry = InquiryModel.objects.create(
       
            name = user,
            user = user,
            product=product,
            status = "Pending",
            **validated_data
        )
        return inquiry

    