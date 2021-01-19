from django.db import transaction
from django.conf import settings
from rest_framework import serializers

from utils.generals import get_model
from apps.shopping.utils.constants import METRIC_CHOICES

Product = get_model('shopping', 'Product')
ProductRate = get_model('shopping', 'ProductRate')
ProductMetric = get_model('shopping', 'ProductMetric')


class ProductMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMetric
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        metric_choice = dict(METRIC_CHOICES)
        ret['metric_display'] = metric_choice.get(instance.metric)
        return ret


class ProductSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    lowest_price = serializers.IntegerField(read_only=True)
    highest_price = serializers.IntegerField(read_only=True)
    average_price = serializers.IntegerField(read_only=True)
    product_metric = ProductMetricSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)
        image = getattr(instance, 'image', None)

        if image:
            ret['image'] = request.build_absolute_uri(settings.MEDIA_URL + image)
        return ret

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
