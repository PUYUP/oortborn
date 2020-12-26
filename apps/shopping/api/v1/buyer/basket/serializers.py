import os

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import slugify

from rest_framework import fields, serializers
from rest_framework.exceptions import NotFound

from utils.generals import get_model
from utils.mixin.validators import CleanValidateMixin
from utils.mixin.api import DynamicFieldsModelSerializer, ExcludeFieldsModelSerializer
from ..purchased.serializers import PurchasedSerializer, PurchasedStuffSerializer

Basket = get_model('shopping', 'Basket')
BasketAttachment = get_model('shopping', 'BasketAttachment')
Stuff = get_model('shopping', 'Stuff')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')
Share = get_model('shopping', 'Share')


def handle_upload_attachment(instance, file):
    if instance and file:
        name, ext = os.path.splitext(file.name)

        fsize = file.size / 1000
        if fsize > 5000:
            raise serializers.ValidationError({'detail': _("Ukuran file maksimal 5 MB")})
    
        if ext != '.jpeg' and ext != '.jpg' and ext != '.png':
            raise serializers.ValidationError({'detail': _("Jenis file tidak diperbolehkan")})

        basket = getattr(instance, 'basket')
        username = basket.user.username
        basket_name = basket.name
        filename = '{username}_{basket_name}'.format(username=username, basket_name=basket_name)
        filename_slug = slugify(filename)

        instance.image.save('%s%s' % (filename_slug, ext), file, save=False)
        instance.save(update_fields=['image'])


class ShareSerializer(CleanValidateMixin, DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:buyer:share-detail',
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
        handle_upload_attachment(obj, image)
        return obj


class BasketSerializer(CleanValidateMixin, ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:buyer:basket-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    purchased = PurchasedSerializer(read_only=True, many=True)
    share = ShareSerializer(read_only=True, many=True,
                                     fields=['uuid', 'status', 'is_admin', 'is_can_crud',
                                             'is_can_buy', 'to_user', 'url'])

    first_name = serializers.CharField(read_only=True, source='user.first_name')
    total_stuff = serializers.IntegerField(read_only=True)
    total_stuff_purchased = serializers.IntegerField(read_only=True)
    total_stuff_found = serializers.IntegerField(read_only=True)
    total_stuff_notfound = serializers.IntegerField(read_only=True)
    total_stuff_looked = serializers.IntegerField(read_only=True)
    total_amount = serializers.IntegerField(read_only=True)
    total_share = serializers.IntegerField(read_only=True)
    total_attachment = serializers.IntegerField(read_only=True)
    
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


class StuffSerializer(CleanValidateMixin, ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:buyer:stuff-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.SlugRelatedField(slug_field='uuid', queryset=get_user_model().objects.all(), default=serializers.CurrentUserDefault())
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    basket = serializers.SlugRelatedField(slug_field='uuid', queryset=Basket.objects.all())
    purchased_stuff = PurchasedStuffSerializer(required=False, exclude_fields=['stuff', 'purchased'])
    is_creator = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Stuff
        fields = '__all__'
    
    def get_is_creator(self, obj):
        request = self.context.get('request')
        return request.user.id == obj.user.id
    
    def to_internal_value(self, data):
        self.purchased_stuff = data.pop('purchased_stuff', None)
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
