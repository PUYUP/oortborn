from django.urls import path, include

# THIRD PARTY
from rest_framework.routers import DefaultRouter

from .product.views import ProductApiView, ProductRateApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('products', ProductApiView, basename='product')
router.register('product-rates', ProductRateApiView, basename='product_rate')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
