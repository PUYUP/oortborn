from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.generals import get_model
from .serializers import PurchasedSerializer, PurchasedStuffSerializer

Purchased = get_model('shopping', 'Purchased')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')


class PurchasedApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = Purchased.objects \
            .prefetch_related('to_user', 'user', 'basket') \
            .select_related('to_user', 'user', 'basket')

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
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)
        
        try:
            queryset.delete(request=request)
        except ValidationError as e:
            raise NotAcceptable(detail=' '.join(e))

        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)


class PurchasedStuffApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = PurchasedStuff.objects \
            .prefetch_related('stuff', 'purchased', 'basket', 'user') \
            .select_related('stuff', 'purchased', 'basket', 'user')

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

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = PurchasedStuffSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

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

    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)
        
        try:
            queryset.delete(request=request)
        except ValidationError as e:
            raise NotAcceptable(detail=' '.join(e))

        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)
