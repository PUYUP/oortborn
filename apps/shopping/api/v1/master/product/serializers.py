import math

from django.db import transaction
from rest_framework import serializers

from utils.generals import get_model, quantity_format

Product = get_model('shopping', 'Product')
ProductRate = get_model('shopping', 'ProductRate')


class ProductSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Product
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = Product.objects.get_or_create(**validated_data)
        return instance


class ProductRateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ProductRate
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['quantity'] = instance.quantity_format
        ret['metric_display'] = instance.get_metric_display()
        return ret
