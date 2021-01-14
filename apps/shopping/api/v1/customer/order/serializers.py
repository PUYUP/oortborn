from utils.mixin.api import DynamicFieldsModelSerializer, ExcludeFieldsModelSerializer, ListSerializerUpdateMappingField, WritetableFieldPutMethod
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings

from rest_framework import serializers

from utils.generals import get_model, quantity_format
from utils.mixin.validators import CleanValidateMixin

Order = get_model('shopping', 'Order')
OrderSchedule = get_model('shopping', 'OrderSchedule')
OrderLine = get_model('shopping', 'OrderLine')
Basket = get_model('shopping', 'Basket')
Assign = get_model('shopping', 'Assign')


class AssignSerializer(CleanValidateMixin, serializers.ModelSerializer):
    assistant_name = serializers.StringRelatedField(many=False, read_only=True,
                                                    source='assistant.first_name')

    class Meta:
        model = Assign
        fields = '__all__'


class OrderScheduleSerializer(CleanValidateMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:order_schedule-detail',
                                               lookup_field='uuid', read_only=True)

    class Meta:
        model = OrderSchedule
        fields = ['url', 'uuid', 'datetime',]


class OrderLineListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    pass


class OrderLineSerializer(CleanValidateMixin, WritetableFieldPutMethod, DynamicFieldsModelSerializer,
                          ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)

    class Meta:
        model = OrderLine
        fields = '__all__'
        list_serializer_class = OrderLineListSerializer
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['quantity'] = instance.quantity_format
        ret['metric_display'] = instance.get_metric_display()
        return ret


class OrderSerializer(CleanValidateMixin, DynamicFieldsModelSerializer,
                      ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    customer = serializers.SlugRelatedField(slug_field='uuid', queryset=get_user_model().objects.all(),
                                            default=serializers.CurrentUserDefault())
    basket = serializers.SlugRelatedField(slug_field='uuid', queryset=Basket.objects.all())
    basket_name = serializers.StringRelatedField(many=False, source='basket.name')
    order_schedule = OrderScheduleSerializer(many=False, required=True)
    assign = AssignSerializer(many=False, read_only=True)
    total_order_line = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        order_schedule = validated_data.pop('order_schedule')
        instance = Order.objects.create(**validated_data)

        if instance and order_schedule:
            OrderSchedule.objects.create(order=instance, **order_schedule)
        
        return instance
