from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .basket.views import StuffApiView, BasketApiView, ShareApiView
from .purchased.views import PurchasedApiView, PurchasedStuffApiView
from .circle.views import CircleApiView
from .order.views import OrderApiView, OrderLineApiView, OrderScheduleApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('baskets', BasketApiView, basename='basket')
router.register('stuffs', StuffApiView, basename='stuff')
router.register('purchaseds', PurchasedApiView, basename='purchased')
router.register('purchased-stuffs', PurchasedStuffApiView, basename='purchased_stuff')
router.register('circles', CircleApiView, basename='circle')
router.register('shares', ShareApiView, basename='share')
router.register('orders', OrderApiView, basename='order')
router.register('order-lines', OrderLineApiView, basename='order_line')
router.register('order-schedules', OrderScheduleApiView, basename='order_schedule')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
