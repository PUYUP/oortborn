import uuid
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from utils.validators import non_python_keyword, identifier_validator


class AbstractAssign(models.Model):
    """ Kemudian staff akan melanjutkan order ke assistant """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='assign_customer', editable=False,
                                 db_index=True)
    assistant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, related_name='assign_assistant', db_index=True)
    order = models.OneToOneField('shopping.Order', on_delete=models.CASCADE,
                                 related_name='assign', db_index=True)
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='assign', editable=False, db_index=True)

    started_at = models.DateTimeField(auto_now=False, blank=True, null=True)
    complete_at = models.DateTimeField(auto_now=False, blank=True, null=True)

    # ketika mulai belanja nilanya True
    # setelah selesai kembali ke False
    is_ongoing = models.BooleanField(default=False, db_index=True)
    # jika sudah selesai nilainya True
    is_complete = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Assign")
        verbose_name_plural = _("Assigns")

    def __str__(self):
        return self.order.number
    
    def save(self, *args, **kwargs):
        self.basket = self.order.basket
        self.customer = self.order.customer
        if hasattr(self.order, 'order_schedule'):
            self.started_at = self.order.order_schedule.datetime
        super().save(*args, **kwargs)


class AbstractAssignTracking(models.Model):
    """ 
    Ketika assistant mulai belanja, record pertama digunakan sebagai
    tanda kapan belanja dimulai
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    assign = models.ForeignKey('shopping.Assign', on_delete=models.CASCADE,
                               related_name='assign', db_index=True)

    location = models.TextField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal(0.0),
                                   db_index=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal(0.0),
                                    db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Assign Tracking")
        verbose_name_plural = _("Assign Trackings")

    def __str__(self):
        return self.location


class AbstractAssignLog(models.Model):
    ADDED = 'added'
    CHANGED = 'changed'
    LOG_EVENTS = (
        (ADDED, _("Added")),
        (CHANGED, _("Changed")),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, null=True)
    update_at = models.DateTimeField(auto_now=True, null=True)

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='assign_log', db_index=True)
    assign = models.ForeignKey('shopping.Assign', on_delete=models.CASCADE,
                               related_name='assign_log', db_index=True)

    column = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField()
    event = models.CharField(choices=LOG_EVENTS, default=ADDED, max_length=25,
                             validators=[non_python_keyword, identifier_validator])

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Assign Log")
        verbose_name_plural = _("Assign Logs")

    def __str__(self):
        return self.new_value
