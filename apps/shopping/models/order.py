import uuid
from decimal import Decimal
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..utils.constants import NOMINAL, WAITING, GENERAL_STATUS, METRIC_CHOICES
from utils.generals import quantity_format, random_string
from utils.validators import non_python_keyword, identifier_validator


class AbstractOrder(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='order', editable=False)
    basket = models.OneToOneField('shopping.Basket', on_delete=models.CASCADE,
                                  related_name='order')

    number = models.CharField(max_length=255, db_index=True, unique=True, editable=False)
    status = models.CharField(choices=GENERAL_STATUS, default=WAITING, max_length=15, db_index=True,
                              validators=[identifier_validator, non_python_keyword])

    is_ongoing = models.BooleanField(default=False, db_index=True)
    is_complete = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return self.number
    
    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        
        # save original values, when model is loaded from database,
        # in a separate attribute on the model
        instance._loaded_values = dict(zip(field_names, values))
        
        return instance

    def clean(self, *args, **kwargs):
        old_basket_id = None
        if not self._state.adding:
            old_basket_id = self._loaded_values.get('basket_id')

        if self.basket.id != old_basket_id and (self.basket.is_purchased or self.basket.is_ordered):
            message = _("Daftar sudah dikirim ke Asisten")
            if self.basket.is_purchased:
                message = _("Daftar sudah dibeli")
            raise ValidationError({'basket': message})
        return super().clean()

    def save(self, *args, **kwargs):
        if not self.pk:
            rand = random_string(8)
            now = timezone.datetime.now()
            timestamp = timezone.datetime.timestamp(now)
            number = '{}{}'.format(rand, int(timestamp))
            self.number = number

        # customer always creator of basket
        self.customer = self.basket.user
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_ongoing or hasattr(self, 'assign') and self.assign:
            raise ValidationError(_("Belanja tidak bisa dibatalkan"))
        
        super().delete()


class AbstractOrderSchedule(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    order = models.OneToOneField('shopping.Order', on_delete=models.CASCADE,
                                 related_name='order_schedule', db_index=True)
    datetime = models.DateTimeField(auto_now=False, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Order Schedule")
        verbose_name_plural = _("Order Schedules")

    def __str__(self):
        return str(self.datetime)

    def clean(self, *args, **kwargs):
        if self.datetime.date() < timezone.now().date() + timedelta(days=1):
            raise ValidationError(_("Tanggal tidak tersedia"))
        return super().clean()


class AbstractOrderLine(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='order_line')
    order = models.ForeignKey('shopping.Order', on_delete=models.CASCADE,
                              related_name='order_line')
    stuff = models.ForeignKey('shopping.Stuff', on_delete=models.CASCADE,
                              related_name='order_line')

    name = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    metric = models.CharField(max_length=15, choices=METRIC_CHOICES,
                              validators=[identifier_validator, non_python_keyword])
    price = models.BigIntegerField(default=0)
    amount = models.BigIntegerField(default=0)
    note = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    
    is_found = models.BooleanField(default=None, null=True, db_index=True)
    is_private = models.BooleanField(default=False, null=True, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Order Line")
        verbose_name_plural = _("Order Lines")

    def __str__(self):
        return self.name

    @property
    def quantity_format(self):
        if self.quantity:
            return quantity_format(quantity=self.quantity)
        return self.quantity

    def clean(self, *args, **kwargs):
        return super().clean()

    def save(self, *args, **kwargs):
        if self.metric != NOMINAL and self.price > 0 and self.quantity > 0:
            self.amount = self.price * self.quantity
        else:
            self.amount = self.price
        
        # Set price and amount to 0 if not found
        if not self.is_found:
            self.price = 0
            self.amount = 0

        super().save(*args, **kwargs)


class AbstractOrderDelivery(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    order = models.OneToOneField('shopping.Order', on_delete=models.CASCADE,
                                 related_name='order_delivery')
    order_schedule = models.ForeignKey('shopping.OrderSchedule', on_delete=models.CASCADE,
                                       related_name='order_schedule')
    shipping_method = models.ForeignKey('shopping.ShippingMethod', on_delete=models.SET_NULL,
                                        related_name='order_delivery', null=True)
    shipping_address = models.ForeignKey('shopping.ShippingAddress', on_delete=models.SET_NULL,
                                         related_name='order_delivery', null=True)
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='order_delivery', 
                                db_index=True)

    recipient_name = models.CharField(max_length=255, null=True, blank=True)
    msisdn = models.CharField(max_length=14, null=True, blank=True)
    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    state = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=7, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal(0.0),
                                   db_index=True, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal(0.0),
                                    db_index=True, null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Order Delivery")
        verbose_name_plural = _("Order Deliveries")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.shipping_address:
            self.recipient_name = self.shipping_address.recipient_name
            self.msisdn = self.shipping_address.msisdn
            self.street_1 = self.shipping_address.street_1
            self.street_2 = self.shipping_address.street_2
            self.city = self.shipping_address.city
            self.state = self.shipping_address.state
            self.country = self.shipping_address.country
            self.postal_code = self.shipping_address.postal_code
            self.latitude = self.shipping_address.latitude
            self.longitude = self.shipping_address.longitude

    def __str__(self):
        return self.order.number
