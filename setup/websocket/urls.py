from django.urls import path

# Channels
from apps.shopping.consumers import BasketConsumer

websocket_urlpatterns = [
    path('ws/basket/<uuid:basket_uuid>/', BasketConsumer.as_asgi()),
]
