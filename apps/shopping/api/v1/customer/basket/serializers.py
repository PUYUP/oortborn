import os
import math

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import slugify

from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError

from utils.generals import get_model
from utils.mixin.validators import CleanValidateMixin
from utils.mixin.api import (
    DynamicFieldsModelSerializer, 
    ExcludeFieldsModelSerializer, 
    ListSerializerUpdateMappingField
)
from ..purchased.serializers import PurchasedSerializer, PurchasedStuffSerializer

Basket = get_model('shopping', 'Basket')
BasketAttachment = get_model('shopping', 'BasketAttachment')
Stuff = get_model('shopping', 'Stuff')
StuffAttachment = get_model('shopping', 'StuffAttachment')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')
Share = get_model('shopping', 'Share')


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
    pass


class ShareSerializer(CleanValidateMixin, DynamicFieldsModelSerializer,
                      ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:share-detail',
                                               lookup_field='uuid', read_only=True)
    msisdn = serializers.CharField(read_only=True, source='to_user.account.msisdn')
    username = serializers.CharField(required=False, source='to_user.username')
    first_name = serializers.CharField(read_only=True, source='to_user.first_name')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
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


class BasketAttachmentSerializer(CleanValidateMixin, serializers.ModelSerializer):
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


class BasketSerializer(CleanValidateMixin, DynamicFieldsModelSerializer,
                       ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:basket-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    purchased = PurchasedSerializer(read_only=True, many=True)
    share = ShareSerializer(read_only=True, many=True,
                                     fields=['uuid', 'status', 'is_admin', 'is_can_crud',
                                             'is_can_buy', 'to_user', 'url'])

    first_name = serializers.CharField(read_only=True, source='user.first_name')
    subtotal_stuff = serializers.IntegerField(read_only=True)
    subtotal_stuff_purchased = serializers.IntegerField(read_only=True)
    subtotal_stuff_found = serializers.IntegerField(read_only=True)
    subtotal_stuff_notfound = serializers.IntegerField(read_only=True)
    subtotal_stuff_looked = serializers.IntegerField(read_only=True)
    subtotal_amount = serializers.IntegerField(read_only=True)
    subtotal_share = serializers.IntegerField(read_only=True)
    subtotal_attachment = serializers.IntegerField(read_only=True)
    
    is_creator = serializers.SerializerMethodField(read_only=True)
    is_share_with_you = serializers.BooleanField(read_only=True)
    is_share_uuid = serializers.UUIDField(read_only=True)
    is_share_sort = serializers.IntegerField(read_only=True)
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
    def update(self, instance, validated_data):
        request = self.context.get('request')

        # If not creator limit update some fields
        if request.user.uuid != instance.user.uuid:
            instance.save(update_fields=['is_complete'])
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


class StuffSerializer(CleanValidateMixin, DynamicFieldsModelSerializer,
                      ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:stuff-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.SlugRelatedField(slug_field='uuid', queryset=get_user_model().objects.all(),
                                        default=serializers.CurrentUserDefault())
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
        quantity = instance.quantity
        if quantity:
            frac, whole = math.modf(instance.quantity)
            quantity_fmt = frac + whole

            if (quantity_fmt % 1 > 0):
                quantity = quantity_fmt
            else:
                quantity = int(quantity_fmt)

        data = super().to_representation(instance)
        data['quantity'] = quantity
        return data

    def to_internal_value(self, data):
        self.purchased_stuff = data.pop('purchased_stuff', None)
        if self.purchased_stuff is not None:
            # Validate amount
            amount = self.purchased_stuff.get('amount', 0)
            if amount <= 0:
                raise ValidationError({'amount': _("Harga tidak boleh kurang dari nol")})
            
            # Validate quantity
            quantity = self.purchased_stuff.get('quantity', 0)
            if quantity <= 0:
                raise ValidationError({'quantity': _("Jumlah tidak boleh kurang dari nol")})

        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        basket = validated_data.get('basket')
        instance = Stuff.objects.create(**validated_data)

        # Execute only after basket mark is_complete
        # This handle user add additional stuff
        if instance and basket.is_complete and self.purchased_stuff:
            # Remove this params because wee need the object from this param
            self.purchased_stuff.pop('basket')
            self.purchased_stuff.pop('purchased')

            # Get purchased from current user
            purchased = basket.purchased.get(user_id=request.user.id)
            PurchasedStuff.objects.create(user=request.user, stuff=instance, basket=basket,
                                          purchased=purchased, **self.purchased_stuff)
            
            instance.is_additional = True
            instance.is_purchased = True
            instance.save()

        instance.refresh_from_db()
        return instance
