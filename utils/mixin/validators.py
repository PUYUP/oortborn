from django.db.models.query import QuerySet
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
        """
        if self.instance:
            if isinstance(self.instance, QuerySet):
                for item in self.instance:
                    y = {t.name: getattr(item, t.name) for t in item._meta.fields}
                    for x in list(y):
                        v = attr.get(x)
                        if v or v == 0:
                            y[x] = v
                    attr = y
            else:
                y = {t.name: getattr(self.instance, t.name) for t in self.instance._meta.fields}
                for x in list(y):
                    v = attr.get(x)
                    if v or v == 0:
                        y[x] = v
                attr = y
        """

        if not self.instance:
            instance = self.Meta.model(**attr)
            if hasattr(instance, 'clean'):
                instance.clean(request=request)
        else:
            if isinstance(self.instance, QuerySet):
                for item in self.instance:
                    item.clean(request=request)
            else:
                self.instance.clean(request=request)

        return attrs
