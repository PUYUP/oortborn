import uuid

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class AbstractCircle(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='circle')
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Circle")
        verbose_name_plural = _("Circles")

    def __str__(self):
        return self.name


class AbstractCircleMember(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    circle = models.ForeignKey('shopping.Circle', on_delete=models.CASCADE,
                               related_name='circle_member')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='circle_member')

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Circle Member")
        verbose_name_plural = _("Circle Members")

    def __str__(self):
        return self.user.username
