from django.urls import path, include

from .customer import routers as customer_routers
from .master import routers as master_routers

urlpatterns = [
    path('customer/', include((customer_routers, 'customer'))),
    path('master/', include((master_routers, 'master'))),
]
