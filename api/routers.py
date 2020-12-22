from django.urls import path, include

from apps.person.api.v1 import routers as person_routers
from apps.shopping.api.v1 import routers as shopping_routers

from api.views import RootApiView

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('person/v1/', include((person_routers, 'person_api'), namespace='person_v1')),
    path('shopping/v1/', include((shopping_routers, 'shopping_api'), namespace='shopping_v1')),
]
