import os
import math

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import fields
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import slugify
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError

from utils.generals import get_model, quantity_format
from utils.mixin.validators import CleanValidateMixin
from utils.mixin.api import (
    CreatableSlugRelatedField, DynamicFieldsModelSerializer, 
    ExcludeFieldsModelSerializer, 
    ListSerializerUpdateMappingField, 
    WritetableFieldPutMethod
)
from ..purchased.serializers import PurchasedSerializer, PurchasedStuffSerializer
from ..order.serializers import OrderSerializer

Basket = get_model('shopping', 'Basket')
BasketAttachment = get_model('shopping', 'BasketAttachment')
Stuff = get_model('shopping', 'Stuff')
StuffAttachment = get_model('shopping', 'StuffAttachment')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')
Share = get_model('shopping', 'Share')
Product = get_model('shopping', 'Product')


def validate_attachment(file):
    name, ext = os.path.splitext(file.name)
    fsize = file.size / 1000
    if fsize > 5000:
        raise serializers.ValidationError({'detail': _("Ukuran file maksimal 5 MB")})

    if ext != '.jpeg' and ext != '.jpg' and ext != '.png':
        raise serializers.ValidationError({'detail': _("Jenis file tidak diperbolehkan")})


def handle_upload_basket_attachment(instance, file):
    if instance and file:
        name, ext = os.path.splitext(file.name)
        validate_attachment(file)

        basket = getattr(instance, 'basket')
        basket_name = basket.name
        filename = '{basket_name}'.format(basket_name=basket_name)
        filename_slug = slugify(filename)

        instance.image.save('%s%s' % (filename_slug, ext), file, save=False)
        instance.save(update_fields=['image'])


def handle_upload_stuff_attachment(instance, file):
    if instance and file:
        name, ext = os.path.splitext(file.name)
        validate_attachment(file)

        stuff = getattr(instance, 'stuff')
        stuff_name = stuff.name
        filename = '{stuff_name}'.format(stuff_name=stuff_name)
        filename_slug = slugify(filename)

        instance.image.save('%s%s' % (filename_slug, ext), file, save=False)
        instance.save(update_fields=['image'])


class ShareListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    def to_representation(self, instance):
        if isinstance(instance, QuerySet) and instance.exists():
            instance = instance.prefetch_related('user', 'to_user', 'basket') \
                .select_related('user', 'to_user', 'basket')
        return super().to_representation(instance)


class ShareSerializer(CleanValidateMixin, WritetableFieldPutMethod, DynamicFieldsModelSerializer,
                      ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:share-detail',
                                               lookup_field='uuid', read_only=True)
    msisdn = serializers.CharField(read_only=True, source='to_user.account.msisdn')
    username = serializers.CharField(required=False, source='to_user.username')
    first_name = serializers.CharField(read_only=True, source='to_user.first_name')
    user = serializers.SlugRelatedField(slug_field='uuid', queryset=get_user_model().objects.all(),
                                        default=serializers.CurrentUserDefault())
    to_user = serializers.SlugRelatedField(slug_field='uuid', queryset=get_user_model().objects.all(), required=False)
    basket = serializers.SlugRelatedField(slug_field='uuid', queryset=Basket.objects.all())

    class Meta:
        model = Share
        fields = '__all__'
        list_serializer_class = ShareListSerializer

    def to_internal_value(self, data):
        username = data.pop('username', None)
        to_user = data.get('to_user', None)

        if username and to_user is None:
            try:
                to_user = get_user_model().objects.get(username=username)
            except ObjectDoesNotExist:
                raise NotFound(detail=_("User {} tidak ditemukan".format(username)))

            data['to_user'] = to_user.uuid

        instance = super().to_internal_value(data)
        return instance

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = Share.objects.get_or_create(**validated_data)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')

        # If not creator of share only update status field
        if request.user.uuid != instance.user.uuid:
            instance.save(update_fields=['status'])
        else:
            instance.save()

        return super().update(instance, validated_data)


class StuffListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    pass


class StuffAttachmentSerializer(CleanValidateMixin, serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    stuff = serializers.SlugRelatedField(slug_field='uuid', queryset=Stuff.objects.all())

    class Meta:
        model = StuffAttachment
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        image = validated_data.pop('image', None)
        obj = StuffAttachment.objects.create(**validated_data)
        handle_upload_stuff_attachment(obj, image)
        return obj


class StuffSerializer(CleanValidateMixin, WritetableFieldPutMethod, DynamicFieldsModelSerializer,
                      ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:stuff-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.SlugRelatedField(slug_field='uuid', queryset=get_user_model().objects.all(),
                                        default=serializers.CurrentUserDefault())
    product = CreatableSlugRelatedField(slug_field='name', queryset=Product.objects.all())
    basket = serializers.SlugRelatedField(slug_field='uuid', queryset=Basket.objects.all())
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    purchased_stuff = PurchasedStuffSerializer(required=False, exclude_fields=['stuff', 'purchased'])
    is_creator = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Stuff
        fields = '__all__'
        list_serializer_class = StuffListSerializer
    
    def get_is_creator(self, obj):
        request = self.context.get('request')
        return request.user.id == obj.user.id

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['quantity'] = instance.quantity_format
        ret['metric_display'] = instance.get_metric_display()
        return ret

    def to_internal_value(self, data):
        self.purchased_stuff = data.pop('purchased_stuff', None)
        if self.purchased_stuff is not None:
            is_found = self.purchased_stuff.get('is_found', False)
            if is_found:
                price = self.purchased_stuff.get('price', 0)
                quantity = self.purchased_stuff.get('quantity', 0)

                if price <= 0:
                    raise ValidationError({'price': _("Harga tidak boleh kurang dari nol")})

                if quantity <= 0:
                    raise ValidationError({'quantity': _("Jumlah tidak boleh kurang dari nol")})

        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        basket = validated_data.get('basket')
        instance = Stuff.objects.create(**validated_data)

        # This handle user add additional stuff
        if instance and basket and self.purchased_stuff:
            # Remove this params because wee need the object from this param
            self.purchased_stuff.pop('basket')
            self.purchased_stuff.pop('purchased')

            # Get purchased from current user
            purchased = basket.purchased.get(user_id=request.user.id)
            PurchasedStuff.objects.create(user=request.user, stuff=instance, basket=basket,
                                          purchased=purchased, **self.purchased_stuff)
            
            if basket.is_complete:
                instance.is_additional = True

            instance.is_purchased = True
            instance.save()

        instance.refresh_from_db()
        return instance


class BasketAttachmentSerializer(CleanValidateMixin, WritetableFieldPutMethod,
                                 serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    basket = serializers.SlugRelatedField(slug_field='uuid', queryset=Basket.objects.all())

    class Meta:
        model = BasketAttachment
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        image = validated_data.pop('image', None)
        obj = BasketAttachment.objects.create(**validated_data)
        handle_upload_basket_attachment(obj, image)
        return obj


class BasketListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    pass


class BasketSerializer(DynamicFieldsModelSerializer, ExcludeFieldsModelSerializer,
                       CleanValidateMixin, serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:basket-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.SlugRelatedField(slug_field='uuid', queryset=get_user_model().objects.all(),
                                        default=serializers.CurrentUserDefault())
    purchased = PurchasedSerializer(read_only=True, many=True)
    stuff = StuffSerializer(many=True, write_only=True, required=False, exclude_fields=['basket'])
    share = ShareSerializer(read_only=True, many=True,
                            exclude_fields=['basket', 'circle', 'msisdn', 'username',
                                            'sort', 'user', 'create_at', 'update_at', 'id'])
    order = OrderSerializer(read_only=True, many=False, fields=['uuid', 'order_schedule'])

    first_name = serializers.CharField(read_only=True, source='user.first_name')
    count_stuff = serializers.IntegerField(read_only=True)
    count_stuff_purchased = serializers.IntegerField(read_only=True)
    count_stuff_found = serializers.IntegerField(read_only=True)
    count_stuff_notfound = serializers.IntegerField(read_only=True)
    count_stuff_looked = serializers.IntegerField(read_only=True)
    count_amount = serializers.IntegerField(read_only=True)
    count_share = serializers.IntegerField(read_only=True)
    count_attachment = serializers.IntegerField(read_only=True)
    
    is_creator = serializers.SerializerMethodField(read_only=True)
    is_share_with_you = serializers.BooleanField(read_only=True)
    is_share_uuid = serializers.UUIDField(read_only=True)
    is_share_sort = serializers.IntegerField(read_only=True)
    is_order_ongoing = serializers.BooleanField(read_only=True)
    """
    is_share_status = serializers.CharField(read_only=True)
    is_share_admin = serializers.BooleanField(read_only=True)
    is_share_can_crud = serializers.BooleanField(read_only=True)
    is_share_can_read = serializers.BooleanField(read_only=True)
    is_share_can_buy = serializers.BooleanField(read_only=True)
    """
    sorted = serializers.IntegerField(read_only=True)

    class Meta:
        model = Basket
        fields = '__all__'
        list_serializer_class = BasketListSerializer

    def get_is_creator(self, obj):
        request = self.context.get('request')
        return request.user.id == obj.user.id

    @transaction.atomic
    def create(self, validated_data):
        stuffs = validated_data.pop('stuff', None)
        instance = Basket.objects.create(**validated_data)

        # create stuffs
        if stuffs and instance:
            stuffs_obj = []
            for item in stuffs:
                stuff_obj = Stuff(basket=instance, **item)
                stuffs_obj.append(stuff_obj)
            
            try:
                Stuff.objects.bulk_create(stuffs_obj, ignore_conflicts=False)
            except Exception as e:
                raise ValidationError(detail=str(e))

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')

        instance.complete_at = timezone.now()
        instance.completed_by = request.user

        # If not creator limit update some fields
        if request.user.uuid != instance.user.uuid:
            instance.save(update_fields=['is_complete', 'completed_by'])
        else:
            instance.save()

        return super().update(instance, validated_data)
