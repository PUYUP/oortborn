from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, NotFound
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.pagination import build_result_pagination
from utils.mixin.viewsets import ViewSetDestroyObjMixin, ViewSetGetObjMixin
from .serializers import PurchasedSerializer, PurchasedStuffSerializer, PurchasedStuffAttachmentSerializer

Purchased = get_model('shopping', 'Purchased')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')
PurchasedStuffAttachment = get_model('shopping', 'PurchasedStuffAttachment')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class PurchasedApiView(ViewSetGetObjMixin, ViewSetDestroyObjMixin, viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = Purchased.objects \
            .prefetch_related('user', 'basket') \
            .select_related('user', 'basket')

        return query

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = PurchasedSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = PurchasedSerializer(data=request.data, many=False, context=context)
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
        serializer = PurchasedSerializer(instance=queryset, data=request.data, partial=True,
                                         many=False, context=context)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

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
        serializer = PurchasedSerializer(queryset, data=request.data, context=context, many=True,
                                         fields=[*used_fields])

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise NotAcceptable(detail=str(e))

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)


class PurchasedStuffApiView(ViewSetGetObjMixin, ViewSetDestroyObjMixin, viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = PurchasedStuff.objects \
            .prefetch_related('stuff', 'purchased', 'basket', 'user') \
            .select_related('stuff', 'purchased', 'basket', 'user')

        return query

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = PurchasedStuffSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = PurchasedStuffSerializer(data=request.data, many=False, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except Exception as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)
        serializer = PurchasedStuffSerializer(instance=queryset, data=request.data, partial=True,
                                              many=False, context=context)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    # List attachment
    @transaction.atomic
    @action(methods=['get', 'post'], detail=True, 
            permission_classes=[IsAuthenticated],
            parser_classes=[MultiPartParser],
            url_path='attachments', 
            url_name='attachment')
    def list_attachment(self, request, uuid=None):
        context = {'request': request}
        method = request.method

        if method == 'GET':
            queryset = self.get_object(uuid=uuid).purchased_stuff_attachment \
                .prefetch_related('user', 'purchased_stuff') \
                .select_related('user', 'purchased_stuff')

            queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
            serializer = PurchasedStuffAttachmentSerializer(queryset_paginator, many=True, context=context)
            pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
            return Response(pagination_result, status=response_status.HTTP_200_OK)

        if method == 'POST':
            serializer = PurchasedStuffAttachmentSerializer(data=request.data, context=context)
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                except ValidationError as e:
                    return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
                return Response(serializer.data, status=response_status.HTTP_200_OK)
            return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # UPDATE, DELETE Attachment
    @transaction.atomic
    @action(methods=['get', 'patch', 'delete'], detail=True,
            permission_classes=[IsAuthenticated],
            parser_classes=[MultiPartParser],
            url_path='attachments/(?P<attachment_uuid>[^/.]+)', 
            url_name='attachment')
    def update_attachment(self, request, uuid=None, attachment_uuid=None):
        context = {'request': request}
        method = request.method

        try:
            queryset = PurchasedStuffAttachment.objects.select_for_update().get(uuid=attachment_uuid)
        except ValidationError as e:
            return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
        except ObjectDoesNotExist:
            raise NotFound()
        
        if method == 'GET':
            serializer = PurchasedStuffAttachmentSerializer(queryset, context=context)
            return Response(serializer.data, status=response_status.HTTP_200_OK)

        elif method == 'PATCH':
            serializer = PurchasedStuffAttachmentSerializer(queryset, data=request.data, partial=True, context=context)
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                except ValidationError as e:
                    return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
                return Response(serializer.data, status=response_status.HTTP_200_OK)
            return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

        elif method == 'DELETE':
            try:
                queryset.delete(request=request)
            except ValidationError as e:
                raise NotAcceptable(detail=' '.join(e))
            return Response({'detail': _("Delete success!")}, status=response_status.HTTP_200_OK)
