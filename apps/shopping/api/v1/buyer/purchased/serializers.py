from django.db import transaction
from django.contrib.auth import get_user_model

from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.api import ExcludeFieldsModelSerializer
from utils.mixin.validators import CleanValidateMixin

Purchased = get_model('shopping', 'Purchased')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')
Basket = get_model('shopping', 'Basket')
Stuff = get_model('shopping', 'Stuff')
User = get_user_model()


class PurchasedListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        source = getattr(self, 'source')
        request = self.context.get('request')
        user = request.user
        
        if source == 'purchased':
            data = data.select_related('to_user', 'basket') \
                .prefetch_related('to_user', 'basket') \
                .filter(to_user_id=user.id)

        return super().to_representation(data)


class PurchasedSerializer(CleanValidateMixin, serializers.ModelSerializer):
    basket = serializers.SlugRelatedField(slug_field='uuid', queryset=Basket.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    to_user = serializers.SlugRelatedField(slug_field='uuid', queryset=User.objects.all())

    class Meta:
        model = Purchased
        # list_serializer_class = PurchasedListSerializer
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = Purchased.objects.get_or_create(**validated_data)
        return instance


class PurchasedStuffSerializer(CleanValidateMixin, ExcludeFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:buyer:purchased_stuff-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
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
