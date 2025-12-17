from rest_framework import serializers
from user_app.models import UserModel


class CustomerSerializer(serializers.ModelSerializer):
    address = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = UserModel
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'mobile_no',
            'firm_name',
            'unpaid_amount',
            'advance_amount',
            'address',
        ]

class SalesPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'first_name', 'last_name', 'email', 'mobile_no', 'firm_name']