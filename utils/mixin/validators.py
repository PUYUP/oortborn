from rest_framework import serializers


class CleanValidateMixin(serializers.ModelSerializer):
    def validate(self, attrs):
        request = self.context.get('request', None)
        instance = self.instance
        if not instance:
            instance = self.Meta.model(**attrs)

        if hasattr(instance, 'clean'):
            instance.clean(request=request)

        return super().validate(attrs)
