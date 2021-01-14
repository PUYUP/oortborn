from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, ValidationError as ValidationErrorResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.pagination import build_result_pagination
from utils.mixin.viewsets import ViewSetDestroyObjMixin, ViewSetGetObjMixin
from apps.shopping.utils.constants import ACCEPT, DONE, WAITING
from .serializers import OrderSerializer, OrderLineSerializer, OrderScheduleSerializer

Order = get_model('shopping', 'Order')
OrderSchedule = get_model('shopping', 'OrderSchedule')
OrderLine = get_model('shopping', 'OrderLine')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class OrderApiView(ViewSetGetObjMixin, ViewSetDestroyObjMixin, viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = Order.objects \
            .prefetch_related('customer', 'basket') \
            .select_related('customer', 'basket', 'assign', 'assign__assistant',
                            'order_schedule') \
            .filter(customer_id=self.request.user.id) \
            .annotate(total_order_line=Count('order_line')) \
            .order_by('-create_at')

        return query

    def list(self, request, format=None):
        context = {'request': request}
        status = request.query_params.get('status', None)
        queryset = self.queryset()

        summary = queryset.aggregate(
            count_waiting=Count('id', filter=Q(status=WAITING)),
            count_accept=Count('id', filter=Q(status=ACCEPT)),
            count_done=Count('id', filter=Q(status=DONE))
        )

        if status is not None:
            queryset = queryset.filter(status=status)

        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = OrderSerializer(queryset_paginator, many=True, context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        pagination_result['summary'] = summary
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = OrderSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = OrderSerializer(data=request.data, many=False, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except Exception as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)


class OrderLineApiView(ViewSetGetObjMixin, ViewSetDestroyObjMixin, viewsets.ViewSet):
    """
    Param GET:
    
        {
            "order_uuid": "uuid4"
        }
    
    Param PUT:

        {
            "uuid": "uuid4",
            "field": "value"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = OrderLine.objects \
            .prefetch_related('customer', 'order', 'stuff') \
            .select_related('customer', 'order', 'stuff') \
            .filter(customer_id=self.request.user.id)

        return query

    def list(self, request, format=None):
        context = {'request': request}
        order_uuid = request.query_params.get('order_uuid', None)
        queryset = self.queryset()

        try:
            queryset = queryset.filter(order__uuid=order_uuid)
        except ValidationError as e:
            raise ValidationErrorResponse({'detail': str(e)})
        
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = OrderLineSerializer(queryset_paginator, many=True, context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, format=None):
        fields = []
        update_uuids = [item.get('uuid') for item in request.data]

        # Collect fields affect for updated
        for item in request.data:
            fields.extend(list(item.keys()))

        queryset = self.queryset().filter(uuid__in=update_uuids)
        if queryset.exists():
            used_fields = [*list(dict.fromkeys(fields))]
        else:
            used_fields = '__all__'
    
        context = {'request': request}
        serializer = OrderLineSerializer(queryset, data=request.data, context=context, many=True,
                                         fields=[*used_fields])

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise NotAcceptable(detail=str(e))

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)


class OrderScheduleApiView(ViewSetGetObjMixin, ViewSetDestroyObjMixin, viewsets.ViewSet):
    """
    Param:

        {
            "datetime": "iso format"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = OrderSchedule.objects \
            .prefetch_related('order', 'order__customer') \
            .select_related('order') \
            .filter(order__customer_id=self.request.user.id)

        return query

    def list(self, request, format=None):
        return Response(status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = OrderScheduleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def partial_update(self, request, uuid=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)
        serializer = OrderScheduleSerializer(instance=queryset, data=request.data, partial=True,
                                             many=False, context=context)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except Exception as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)
