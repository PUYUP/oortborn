from dateutil import parser

from django.db import transaction
from django.db.models import Count, Sum, Q, F, Exists, Subquery, OuterRef, Case, When, IntegerField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.utils import timezone

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError as ValidationErrorResponse
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from utils.generals import get_model
from utils.pagination import build_result_pagination
from .serializers import BasketAttachmentSerializer, BasketSerializer, StuffSerializer, ShareSerializer

Basket = get_model('shopping', 'Basket')
BasketAttachment = get_model('shopping', 'BasketAttachment')
Stuff = get_model('shopping', 'Stuff')
Share = get_model('shopping', 'Share')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


"""
START BASKET
"""

class BasketApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        date = self.request.query_params.get('date', None)
        share_obj = Share.objects.filter(basket__uuid=OuterRef('uuid'), to_user_id=self.request.user.id)
        basket_obj = Basket.objects \
            .prefetch_related('stuff', 'stuff__purchased_stuff') \
            .filter(uuid=OuterRef('uuid')).annotate(total_amount=Sum('stuff__purchased_stuff__amount')).values('total_amount')

        query = Basket.objects \
            .prefetch_related('user', 'stuff', 'stuff__purchased_stuff', 'purchased',
                              'purchased__basket', 'purchased__user', 'purchased__schedule',
                              'share', 'share__to_user', 'share__basket') \
            .select_related('user') \
            .annotate(
                subtotal_stuff=Count('stuff', distinct=True),
                subtotal_stuff_purchased=Count('stuff', distinct=True, filter=Q(stuff__purchased_stuff__isnull=False)),
                subtotal_stuff_found=Count('stuff', distinct=True, filter=Q(stuff__purchased_stuff__is_found=True)),
                subtotal_stuff_notfound=Count('stuff', distinct=True, filter=Q(stuff__purchased_stuff__is_found=False)),
                subtotal_share=Count('share', distinct=True),
                subtotal_attachment=Count('basket_attachment', distinct=True),
                subtotal_stuff_looked=F('subtotal_stuff') - F('subtotal_stuff_purchased'),
                subtotal_amount=Subquery(basket_obj.values('total_amount')[:1]),
                
                is_share_with_you=Exists(share_obj),
                is_share_uuid=Subquery(share_obj.values('uuid')[:1]),
                is_share_sort=Subquery(share_obj.values('sort')[:1]),
                # is_share_status=Subquery(share_obj.values('status')[:1]),
                # is_share_admin=Subquery(share_obj.values('is_admin')[:1]),
                # is_share_can_crud=Subquery(share_obj.values('is_can_crud')[:1]),
                # is_share_can_read=Subquery(share_obj.values('is_can_read')[:1]),
                # is_share_can_buy=Subquery(share_obj.values('is_can_buy')[:1]),
                sorted=Case(
                    When(is_share_sort__isnull=False, then=F('is_share_sort')),
                    When(is_complete=True, then=F('complete_sort')),
                    default=F('sort'),
                    output_field=IntegerField()
                )
            ) \
            .filter(
                Q(user_id=self.request.user.id) 
                | Q(purchased__user_id=self.request.user.id)
                | Q(share__to_user_id=self.request.user.id)
            )

        if date:
            dt = parser.parse(date)
            my_datetime = timezone.make_aware(dt, timezone.get_current_timezone())
            query = query.filter(create_at__gte=my_datetime)

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
            raise ValidationErrorResponse(detail=str(e))

        return query

    def list(self, request, format=None):
        context = {'request': request}
        is_complete = request.query_params.get('is_complete')
        keyword = request.query_params.get('keyword')
        queryset = self.queryset().order_by('sorted')

        if is_complete == 'true':
            queryset = queryset.filter(is_complete=True)
        elif is_complete == 'false':
            queryset = queryset.filter(is_complete=False)

        if keyword:
            queryset = queryset.filter(name__icontains=keyword)

        # Calculate total ampunt
        summary = queryset.aggregate(total_amount=Sum('subtotal_amount'))

        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = BasketSerializer(queryset_paginator, many=True, context=context,
                                      exclude_fields=['share', 'purchased'])
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        pagination_result['summary'] = summary
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = BasketSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = BasketSerializer(data=request.data, many=False, context=context)
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
        serializer = BasketSerializer(instance=queryset, data=request.data, partial=True,
                                      many=False, context=context)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise ValidationErrorResponse(detail=str(e))
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
        serializer = BasketSerializer(queryset, data=request.data, context=context, many=True,
                                      fields=[*used_fields])

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise NotAcceptable(detail=str(e))

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)

    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)

        try:
            queryset.delete(request=request)
        except ValidationError as e:
            raise NotAcceptable(detail=' '.join(e))

        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)

    # Reuse Basket
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated],
            url_path='reuse', url_name='reuse')
    def reuse(self, request, uuid=None):
        context = {'request': request}
        basket = self.get_object(uuid=uuid)
        
        if basket:
            name = basket.name
            note = basket.note
            location = basket.location
            stuffs = basket.stuff \
                .prefetch_related('basket', 'product', 'purchased_stuff', 'purchased_stuff__purchased',
                                  'purchased_stuff__basket') \
                .select_related('basket', 'product')
                
            # Create new basket
            basket_new = Basket.objects.create(user=request.user, name=name, note=note, location=location)
            if basket_new and stuffs.exists():
                # Bulk create stuffs
                bulk_stuffs = []
                for item in stuffs:
                    name = getattr(item, 'name')
                    product = getattr(item, 'product')
                    metric = getattr(item, 'metric')
                    quantity = getattr(item, 'quantity')
                    note = getattr(item, 'note')
                    location = getattr(item, 'location')

                    obj = Stuff(user=request.user, basket=basket_new, product=product, metric=metric,
                                   quantity=quantity, name=name, note=note, location=location)
                    bulk_stuffs.append(obj)
                
                if bulk_stuffs:
                    try:
                        Stuff.objects.bulk_create(bulk_stuffs, ignore_conflicts=False)
                    except Exception as e:
                        raise NotAcceptable(detail=str(e))
                
                serializer = BasketSerializer(basket_new, many=False, context=context)
                return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(status=response_status.HTTP_200_OK)

    # Check Basket has zero price PurchasedStuff
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['get'], detail=True, 
            permission_classes=[IsAuthenticated],
            url_path='check-purchased-stuff', 
            url_name='check_purchased_stuff')
    def check_purchased_stuff(self, request, uuid=None):
        queryset = PurchasedStuff.objects.filter(basket__uuid=uuid, is_found=True)
        total = queryset.count()
        amount_empty = queryset.filter(amount=0).count()

        return Response({
            'detail': _("Ada {} item belum dimasukkan harga (Rp 0)".format(amount_empty)),
            'total': total,
            'amount_empty': amount_empty
        }, status=response_status.HTTP_204_NO_CONTENT)

    # List attachment
    @method_decorator(never_cache)
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
            queryset = self.get_object(uuid=uuid).basket_attachment \
                .prefetch_related('user', 'basket') \
                .select_related('user', 'basket')

            queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
            serializer = BasketAttachmentSerializer(queryset_paginator, many=True, context=context)
            pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
            return Response(pagination_result, status=response_status.HTTP_200_OK)

        if method == 'POST':
            serializer = BasketAttachmentSerializer(data=request.data, context=context)
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                except ValidationError as e:
                    return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
                return Response(serializer.data, status=response_status.HTTP_200_OK)
            return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # UPDATE, DELETE Attachment
    @method_decorator(never_cache)
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
            queryset = BasketAttachment.objects.select_for_update().get(uuid=attachment_uuid)
        except ValidationError as e:
            return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
        except ObjectDoesNotExist:
            raise NotFound()
        
        if method == 'GET':
            serializer = BasketAttachmentSerializer(queryset, context=context)
            return Response(serializer.data, status=response_status.HTTP_200_OK)

        elif method == 'PATCH':
            serializer = BasketAttachmentSerializer(queryset, data=request.data, partial=True, context=context)
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
            return Response({'detail': _("Delete success!")}, status=response_status.HTTP_204_NO_CONTENT)


"""
START STUFF
"""

class StuffApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = Stuff.objects \
            .prefetch_related('basket', 'basket__share', 'product', 'purchased_stuff',
                              'purchased_stuff__purchased', 'purchased_stuff__basket', 
                              'purchased_stuff__user', 'user') \
            .select_related('basket', 'product', 'user') \
            .filter(
                Q(basket__user_id=self.request.user.id)
                | Q(basket__purchased__user_id=self.request.user.id)
                | Q(basket__share__to_user_id=self.request.user.id)
            ).distinct()
        
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
            raise ValidationErrorResponse(detail=str(e))

        return query

    def list(self, request, format=None):
        context = {'request': request}
        status = request.query_params.get('status', None)
        amount = request.query_params.get('amount', None)
        basket_uuid = request.query_params.get('basket_uuid', None)
        date = request.query_params.get('date', None)
        keyword = request.query_params.get('keyword', None)
        is_history = request.query_params.get('is_history', 'false')

        queryset = self.queryset()

        if date:
            dt = parser.parse(date)
            my_datetime = timezone.make_aware(dt, timezone.get_current_timezone())
            queryset = queryset.filter(create_at__gte=my_datetime)
    
        if amount:
            amount_int = int(amount)
            queryset = queryset.filter(purchased_stuff__amount=amount_int)

        if keyword:
            queryset = queryset.filter(name__icontains=keyword)

        if is_history == 'true':
            queryset = queryset.filter(purchased_stuff__isnull=False)

        # Calculate total ampunt
        summary = queryset.aggregate(total_amount=Sum('purchased_stuff__amount'))

        try:
            if status == 'found' or status == 'notfound':
                queryset = queryset.filter(purchased_stuff__isnull=False)
                if status == 'found':
                    queryset = queryset.filter(purchased_stuff__is_found=True)
                elif status == 'notfound':
                    queryset = queryset.filter(purchased_stuff__is_found=False)
            elif status == 'looked':
                queryset = queryset.filter(purchased_stuff__isnull=True)

            if basket_uuid:
                queryset = queryset.filter(basket__uuid=basket_uuid)
        except ValidationError as e:
            raise ValidationErrorResponse(detail=str(e))

        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = StuffSerializer(queryset_paginator, many=True, context=context,
                                     exclude_fields=['basket'])
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        pagination_result['summary'] = summary
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = StuffSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = StuffSerializer(data=request.data, many=False, context=context)
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
        serializer = StuffSerializer(instance=queryset, data=request.data, partial=True,
                                     many=False, context=context)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise ValidationErrorResponse(detail=str(e))
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
        serializer = StuffSerializer(queryset, data=request.data, context=context, many=True,
                                     fields=used_fields)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise NotAcceptable(detail=str(e))

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)

    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)

        try:
            queryset.delete(request=request)
        except ValidationError as e:
            raise NotAcceptable(detail=' '.join(e))

        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)


"""
START SHARE WITH
"""

class ShareApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def queryset(self):
        query = Share.objects \
            .prefetch_related('to_user', 'to_user__account', 'basket') \
            .select_related('to_user', 'basket') \
            .filter(Q(user__uuid=self.request.user.uuid)
                    | Q(to_user_id=self.request.user.id))

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
            raise ValidationErrorResponse(detail=str(e))

        return query

    def list(self, request, format=None):
        context = {'request': request}
        basket_uuid = request.query_params.get('basket_uuid', None)
        queryset = self.queryset()

        if not basket_uuid:
            raise NotAcceptable(detail=_("Basket UUID required"))
            
        try:
            queryset = queryset.filter(basket__uuid=basket_uuid)
        except ValidationError as e:
            raise ValidationErrorResponse(detail=str(e))

        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ShareSerializer(queryset_paginator, many=True, context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = ShareSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ShareSerializer(data=request.data, many=False, context=context)
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
        serializer = ShareSerializer(instance=queryset, data=request.data, partial=True,
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
        serializer = ShareSerializer(queryset, data=request.data, context=context, many=True,
                                     fields=[*used_fields])

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                raise NotAcceptable(detail=str(e))

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)

    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)
        
        try:
            queryset.delete(request=request)
        except ValidationError as e:
            raise NotAcceptable(detail=' '.join(e))

        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)
