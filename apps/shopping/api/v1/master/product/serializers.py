from django.db import transaction
from rest_framework import serializers

from utils.generals import get_model

Product = get_model('shopping', 'Product')
ProductRate = get_model('shopping', 'ProductRate')


class ProductSerializer(serializers.ModelSerializer):
    submitter = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Product
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = Product.objects.get_or_create(**validated_data)
        return instance


class ProductRateSerializer(serializers.ModelSerializer):
    submitter = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ProductRate
        fields = '__all__'
