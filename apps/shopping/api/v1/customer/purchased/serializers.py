import os
import math

from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.template.defaultfilters import slugify

from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.api import (
    DynamicFieldsModelSerializer, 
    ExcludeFieldsModelSerializer, 
    ListSerializerUpdateMappingField, 
    WritetableFieldPutMethod
)
from utils.mixin.validators import CleanValidateMixin

Purchased = get_model('shopping', 'Purchased')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')
PurchasedStuffAttachment = get_model('shopping', 'PurchasedStuffAttachment')
Basket = get_model('shopping', 'Basket')
Stuff = get_model('shopping', 'Stuff')
User = get_user_model()


def validate_attachment(file):
    name, ext = os.path.splitext(file.name)
    fsize = file.size / 1000
    if fsize > 5000:
        raise serializers.ValidationError({'detail': _("Ukuran file maksimal 5 MB")})

    if ext != '.jpeg' and ext != '.jpg' and ext != '.png':
        raise serializers.ValidationError({'detail': _("Jenis file tidak diperbolehkan")})


def handle_upload_purchased_stuff_attachment(instance, file):
    if instance and file:
        name, ext = os.path.splitext(file.name)
        validate_attachment(file)

        parent = getattr(instance, 'purchased_stuff')
        name = parent.name
        filename = '{name}'.format(name=name)
        filename_slug = slugify(filename)

        instance.image.save('%s%s' % (filename_slug, ext), file, save=False)
        instance.save(update_fields=['image'])


class PurchasedListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    def to_representation(self, data):
        if isinstance(data, QuerySet) and data.exists():
            data = data.prefetch_related('user', 'schedule', 'basket') \
                .select_related('user', 'schedule', 'basket')
        return super().to_representation(data)


class PurchasedSerializer(CleanValidateMixin, WritetableFieldPutMethod, DynamicFieldsModelSerializer,
                          ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    basket = serializers.SlugRelatedField(slug_field='uuid', queryset=Basket.objects.all())
    user = serializers.SlugRelatedField(slug_field='uuid', queryset=User.objects.all(),
                                        default=serializers.CurrentUserDefault())

    class Meta:
        model = Purchased
        fields = '__all__'
        list_serializer_class = PurchasedListSerializer

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = Purchased.objects.get_or_create(**validated_data)
        return instance


class PurchasedStuffAttachmentSerializer(CleanValidateMixin, serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    purchased_stuff = serializers.SlugRelatedField(slug_field='uuid', queryset=PurchasedStuff.objects.all())

    class Meta:
        model = PurchasedStuffAttachment
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        image = validated_data.pop('image', None)
        obj = PurchasedStuffAttachment.objects.create(**validated_data)
        handle_upload_purchased_stuff_attachment(obj, image)
        return obj


class PurchasedStuffSerializer(CleanValidateMixin, WritetableFieldPutMethod, ExcludeFieldsModelSerializer,
                               serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:purchased_stuff-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.SlugRelatedField(slug_field='uuid', queryset=User.objects.all(),
                                        default=serializers.CurrentUserDefault())
    basket = serializers.SlugRelatedField(slug_field='uuid', queryset=Basket.objects.all())
    purchased = serializers.SlugRelatedField(slug_field='uuid', queryset=Purchased.objects.all())
    stuff = serializers.SlugRelatedField(slug_field='uuid', queryset=Stuff.objects.all())
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    is_creator = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchasedStuff
        fields = '__all__'

    def get_is_creator(self, obj):
        request = self.context.get('request')
        return request.user.id == obj.user.id

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['quantity'] = instance.quantity_format
        ret['metric_display'] = instance.get_metric_display()
        return ret
