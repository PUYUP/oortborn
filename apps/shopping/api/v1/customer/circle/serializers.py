from rest_framework import serializers

from utils.generals import get_model

Circle = get_model('shopping', 'Circle')


class CircleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='shopping_api:customer:circle-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Circle
        fields = '__all__'
