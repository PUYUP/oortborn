from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from utils.generals import get_model
from utils.pagination import build_result_pagination
from ....permissions import IsObjectOwnerOrReject
from .serializers import CircleSerializer

Circle = get_model('shopping', 'Circle')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class CircleApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsObjectOwnerOrReject,)

    def queryset(self):
        query = Circle.objects \
            .prefetch_related('user') \
            .select_related('user')

        return query

    def get_object(self, uuid=None, is_update=False):
        query = self.queryset()

        try:
            if is_update:
                query = query.select_for_update().get(uuid=uuid)
            else:
                query = query.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()
        except ValidationError as e:
            raise NotAcceptable(detail=str(e))

        return query

    def list(self, request, format=None):
        context = {'request': request}
        queryset = self.queryset()

        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = CircleSerializer(queryset_paginator, many=True, context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = CircleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = CircleSerializer(data=request.data, many=False, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except Exception as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = CircleSerializer(instance=queryset, data=request.data, partial=True,
                                      many=False, context=context)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)
        
        self.check_object_permissions(request, queryset)

        queryset.delete()
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)
