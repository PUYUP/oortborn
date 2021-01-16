import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ..utils.constants import METRIC_CHOICES
from utils.generals import quantity_format
from utils.validators import non_python_keyword, identifier_validator


class AbstractCategory(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.name


class AbstractBrand(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")

    def __str__(self):
        return self.name


class AbstractProduct(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             related_name='product', null=True, blank=True)
    brand = models.ForeignKey('shopping.Brand', on_delete=models.SET_NULL,
                              related_name='product', null=True, blank=True)
    category = models.ForeignKey('shopping.Category', on_delete=models.SET_NULL,
                                 related_name='product', null=True, blank=True)

    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)
    is_catalog = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __str__(self):
        return self.name


class AbstractProductMetric(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    product = models.ForeignKey('shopping.Product', on_delete=models.CASCADE,
                                related_name='product_metric')
    metric = models.CharField(max_length=15, choices=METRIC_CHOICES,
                              validators=[identifier_validator, non_python_keyword])
    
    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Product Metric")
        verbose_name_plural = _("Product Metrics")

    def __str__(self):
        return self.get_metric_display()


class AbstractProductRate(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             related_name='product_rate', null=True, blank=True)
    product = models.ForeignKey('shopping.Product', on_delete=models.SET_NULL,
                                related_name='product_rate', null=True, blank=True)
    purchased_stuff = models.ForeignKey('shopping.PurchasedStuff', on_delete=models.SET_NULL,
                                        related_name='product_rate', null=True, blank=True)

    name = models.CharField(max_length=255, db_index=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    metric = models.CharField(max_length=15, choices=METRIC_CHOICES, default=None,
                              null=True, blank=True, validators=[identifier_validator, non_python_keyword])
    # price divided by amount and quantity
    # eg: amount 6000 / quantity 6 = 1000
    price = models.BigIntegerField(default=0)
    location = models.CharField(max_length=255, null=True, blank=True)
    # some reason user won't share to public
    is_private = models.BooleanField(default=False, null=True, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Product Rate")
        verbose_name_plural = _("Product Rates")

    def __str__(self):
        return self.name
    
    @property
    def quantity_format(self):
        if self.quantity:
            return quantity_format(quantity=self.quantity)
        return self.quantity

    def clean(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request:
            self.quantity = self.request.data.get('quantity', 0)

        if self.quantity <= 0:
            raise ValidationError({'quantity': _("Jumlah tidak boleh kurang dari nol")})
        return super().clean()


class AbstractProductAttachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    product = models.ForeignKey('shopping.Product', on_delete=models.CASCADE,
                                related_name='product_attachment', db_index=True)

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='files/product-attachment/', max_length=500,
                            null=True, blank=True)
    image = models.FileField(upload_to='images/product-attachment/', max_length=500,
                             null=True, blank=True)
    mime = models.CharField(max_length=225)
    sort = models.IntegerField(default=1)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Product Attachment")
        verbose_name_plural = _("Product Attachments")

    def __str__(self):
        return self.name
