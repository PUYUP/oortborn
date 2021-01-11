import uuid

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from ..utils.constants import INVOICE_STATUS, SENT, METRIC_CHOICES
from utils.generals import quantity_format, random_string
from utils.validators import non_python_keyword, identifier_validator


class AbstractInvoice(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='invoice', db_index=True)
    order = models.OneToOneField('shopping.Order', on_delete=models.CASCADE,
                                 related_name='invoice', db_index=True)

    number = models.CharField(max_length=255, editable=False, unique=True, null=True, db_index=True)
    status = models.CharField(max_length=15, choices=INVOICE_STATUS, default=SENT, db_index=True,
                              validators=[identifier_validator, non_python_keyword])

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.assistant = self.order.assistant

        if not self.pk:
            rand = random_string(8)
            now = timezone.datetime.now()
            timestamp = timezone.datetime.timestamp(now)
            number = 'INV{}{}'.format(rand, int(timestamp))
            self.number = number

        super().save(*args, **kwargs)


class AbstractInvoiceLine(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='invoice_line', db_index=True)
    invoice = models.ForeignKey('shopping.Invoice', on_delete=models.CASCADE,
                                related_name='invoice_line', db_index=True)
    order_line = models.OneToOneField('shopping.OrderLine', on_delete=models.CASCADE,
                                      related_name='invoice_line', db_index=True)
    
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    metric = models.CharField(max_length=15, choices=METRIC_CHOICES,
                              validators=[identifier_validator, non_python_keyword])
    price = models.BigIntegerField(default=0)
    amount = models.BigIntegerField(default=0)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Invoice Line")
        verbose_name_plural = _("Invoice Lines")

    def __str__(self):
        return self.order_line.name

    @property
    def quantity_format(self):
        if self.quantity:
            return quantity_format(quantity=self.quantity)
        return self.quantity
