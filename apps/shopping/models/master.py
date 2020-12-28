import uuid

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ..utils.constants import METRIC_CHOICES


class AbstractBrand(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)

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
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  related_name='product', null=True, blank=True)
    brand = models.ForeignKey('shopping.Brand', on_delete=models.SET_NULL,
                              related_name='product', null=True, blank=True)

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __str__(self):
        return self.name


class AbstractProductRate(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  related_name='product_rate', null=True, blank=True)
    product = models.ForeignKey('shopping.Product', on_delete=models.SET_NULL,
                                related_name='product_rate', null=True, blank=True)
    purchased_stuff = models.ForeignKey('shopping.PurchasedStuff', on_delete=models.SET_NULL,
                                        related_name='product_rate', null=True, blank=True)

    name = models.CharField(max_length=255)
    quantity = models.CharField(max_length=255, null=True, blank=True)
    metric = models.CharField(max_length=15, choices=METRIC_CHOICES, default=None,
                              null=True, blank=True)
    # price divided by amount and quantity
    # eg: amount 6000 / quantity 6 = 1000
    price = models.BigIntegerField(default=0)
    location = models.CharField(max_length=255, null=True, blank=True)
    # some reason user won't share to public
    is_private = models.BooleanField(default=False, null=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Product Rate")
        verbose_name_plural = _("Product Rates")

    def __str__(self):
        return self.name


class AbstractProductAttachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    product = models.ForeignKey('shopping.Product', on_delete=models.CASCADE,
                                related_name='product_attachment')

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
