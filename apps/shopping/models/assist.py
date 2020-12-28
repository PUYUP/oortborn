import uuid

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ..utils.constants import WAITING, GENERAL_STATUS


class AbstractOrder(models.Model):
    """ User meminta daftar belanjanya dibelikan """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='order')
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='order')

    # kapan mau diantar?
    datetime = models.DateTimeField(auto_now=False)
    status = models.CharField(choices=GENERAL_STATUS, default=WAITING, max_length=15)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Assistant Order")
        verbose_name_plural = _("Assistant Orders")

    def __str__(self):
        return self.customer.username


class AbstractAssistant(models.Model):
    """ Kemudian staff akan melanjutkan order ke operator """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    # who accept order
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='assistant_staff')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='assistant_user', editable=False)
    # who going to buy
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, related_name='assistant_operator')
    order = models.ForeignKey('shopping.Order', on_delete=models.CASCADE,
                              related_name='assistant')
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='assistant', editable=False)

    started_at = models.DateTimeField(auto_now=False, blank=True, null=True)
    complete_at = models.DateTimeField(auto_now=False, blank=True, null=True)

    # ketika mulai belanja nilanya True
    # setelah selesai kembali ke False
    is_ongoing = models.BooleanField(default=False)
    # jika sudah selesai nilainya True
    is_complete = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Assistant")
        verbose_name_plural = _("Assistants")

    def save(self, *args, **kwargs):
        self.basket = self.order.basket
        self.user = self.order.user
        super().save(*args, **kwargs)


class AbstractAssistantTracking(models.Model):
    """ 
    Ketika operator mulai belanja, record pertama digunakan sebagai
    tanda kapan belanja dimulai
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    assistant = models.ForeignKey('shopping.Assistant', on_delete=models.CASCADE,
                                  related_name='assistant')

    location = models.TextField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=0.0)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Assistant Tracking")
        verbose_name_plural = _("Assistant Trackings")

    def __str__(self):
        return self.location
