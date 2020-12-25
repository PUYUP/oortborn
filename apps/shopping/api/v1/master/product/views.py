import datetime
from dateutil import parser

from django.db.models.functions import Round
from django.db import transaction
from django.db.models import Count, Max, Min, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import ProductSerializer, ProductRateSerializer

Product = get_model('shopping', 'Product')
ProductRate = get_model('shopping', 'ProductRate')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class ProductApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = Product.objects \
            .prefetch_related('brand') \
            .select_related('brand') \
            .values('name') \
            .annotate(product_count=Count('name')) \
            .order_by('name') \
            .distinct()
        
        return query

    def list(self, request, format=None):
        context = {'request': request}
        queryset = self.queryset()

        keyword = request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(name__icontains=keyword)
        
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ProductSerializer(queryset_paginator, many=True, context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ProductSerializer(data=request.data, many=False, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except Exception as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)


class ProductRateApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = ProductRate.objects \
            .prefetch_related('product', 'purchased_stuff') \
            .select_related('product', 'purchased_stuff') \
        
        return query

    def list(self, request, format=None):
        context = {'request': request}
        summary = None
        date = request.query_params.get('date', None)
        keyword = request.query_params.get('keyword')
        queryset = self.queryset().filter(price__gt=0, is_private=False)

        if date:
            dt = parser.parse(date)
            my_datetime = timezone.make_aware(dt, timezone.get_current_timezone())
            queryset = queryset.filter(update_at__range=(my_datetime, my_datetime + datetime.timedelta(days=1)))

        if keyword:
            queryset = queryset.filter(name__icontains=keyword)
            summary = queryset.aggregate(
                highest_price=Max('price'),
                lowest_price=Min('price', filter=Q(price__gt=0)),
                average_price=Round(Avg('price', filter=Q(price__gt=0)))
            )
    
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ProductRateSerializer(queryset_paginator, many=True, context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)

        if summary:
            pagination_result['summary'] = summary

        return Response(pagination_result, status=response_status.HTTP_200_OK)
