from django.forms.models import model_to_dict
from rest_framework import serializers


class CleanValidateMixin(serializers.ModelSerializer):
    def validate(self, attrs):
        request = self.context.get('request')
        
        # exclude all field with type list or dict
        attr = {
            x: attrs.get(x) for x in list(attrs) 
            if not isinstance(attrs.get(x), list) and not isinstance(attrs.get(x), dict)
        }

        # add current instance value
        if self.instance:
            d = self.instance.__dict__
            y = {t: d.get(t) for t in d if not t.startswith('_')}
            for x in y:
                v = attr.get(x)
                if v or v == 0:
                    y[x] = v
            attr = y

        instance = self.Meta.model(**attr)
        if hasattr(instance, 'clean'):
            instance.clean(request=request)

        return attrs
