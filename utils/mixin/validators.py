from django.http import request
from rest_framework import serializers


class CleanValidateMixin(serializers.ModelSerializer):
    def validate(self, attrs):
        request = self.context.get('request')
        
        # exclude all field with type list or dict
        attr = {
            x: attrs.get(x) for x in list(attrs) 
            if not isinstance(attrs.get(x), list) and not isinstance(attrs.get(x), dict)
        }

        instance = self.instance
        if not instance:
            instance = self.Meta.model(**attr)

        if hasattr(instance, 'clean'):
            instance.clean(request=request)

        return super().validate(attrs)
