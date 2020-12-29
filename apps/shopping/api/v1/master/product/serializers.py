import math

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

    def to_representation(self, instance):
        quantity = instance.quantity
        frac, whole = math.modf(instance.quantity)
        quantity_fmt = frac + whole

        if (quantity_fmt % 1 > 0):
            quantity = quantity_fmt
        else:
            quantity = int(quantity_fmt)

        data = super().to_representation(instance)
        data['quantity'] = quantity
        return data
