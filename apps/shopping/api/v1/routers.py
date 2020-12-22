from django.urls import path, include

from .buyer import routers as buyer_routers
from .master import routers as master_routers

urlpatterns = [
    path('buyer/', include((buyer_routers, 'buyer'))),
    path('master/', include((master_routers, 'master'))),
]
