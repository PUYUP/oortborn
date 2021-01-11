import uuid
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ..utils.constants import MOTORCYCLE, VEHICLE_CHOICE


class AbstractShippingAddress(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='shipping_address', db_index=True)

    recipient_name = models.CharField(max_length=255)
    msisdn = models.CharField(max_length=14)
    street_1 = models.TextField()
    street_2 = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=255, db_index=True)
    state = models.CharField(max_length=255, db_index=True)
    country = models.CharField(max_length=255, default=_("Indonesia"))
    postal_code = models.CharField(max_length=7, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal(0.0),
                                   db_index=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal(0.0),
                                    db_index=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Shipping Address")
        verbose_name_plural = _("Shipping Address")

    def __str__(self):
        return '{}: {}'.format(self.recipient_name, self.street_1)
    
    def save(self, *args, **kwargs):
        # If current address mark as primary
        # old address mark is_primary to False
        old_objs = self.__class__.objects.filter(customer_id=self.customer.id, is_primary=True)
        if self.is_primary and old_objs.exists():
            old_objs.update(is_primary=False)
        super().save(*args, **kwargs)


class AbstractShippingMethod(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)
    
    carrier = models.CharField(max_length=255, help_text=_("Eg: Gojek, Grab"))
    vehicle = models.CharField(choices=VEHICLE_CHOICE, default=MOTORCYCLE, max_length=25)
    delievery_time = models.IntegerField(help_text=_("In day"))
    cost = models.BigIntegerField()
    is_enabled = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")

    def __str__(self):
        return self.carrier
