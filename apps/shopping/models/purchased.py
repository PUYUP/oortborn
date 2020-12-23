import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ..utils.constants import METRIC_CHOICES, NOMINAL


class AbstractPurchased(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='purchased')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='purchased_user')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='purchased_to_user')
    schedule = models.ForeignKey('shopping.Schedule', on_delete=models.SET_NULL,
                                 related_name='purchased', null=True, blank=True)

    started_at = models.DateTimeField(auto_now=False, blank=True, null=True)
    complete_at = models.DateTimeField(auto_now=False, blank=True, null=True)
    is_ongoing = models.BooleanField(default=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Purchased")
        verbose_name_plural = _("Purchaseds")

    def __str__(self):
        return self.basket.name
    
    def check_can_add(self):
        """ Jika current user bukan creator Basket cek boleh membeli atau tidak """
        if self.basket.user.uuid != self.current_user.uuid:
            is_can_buy = self.share.filter(is_can_buy=True).exists()
            if not self.share.exists() or not is_can_buy:
                raise ValidationError({'detail': _("Tidak diizinkan melakukan pembelian")})
    
    def check_can_update(self):
        """ Jika current user bukan creator maka tidak boleh update """
        if self.user.uuid != self.current_user.uuid:
            raise ValidationError({'detail': _("Tidak diizinkan merubah")})
    
    def check_can_delete(self):
        """ Hanya bisa dihapus oleh creator """
        if self.user.uuid != self.current_user.uuid:
            raise ValidationError("Tidak diizinkan menghapus")

    def clean(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request:
            self.current_user = self.request.user
            self.share = self.basket.share.filter(to_user_id=self.current_user.id)

            if self.pk:
                self.check_can_update()
            else:
                self.check_can_add()

        return super().clean()
    
    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request is not None:
            self.current_user = self.request.user
            self.check_can_delete()

        super().delete(*args, **kwargs)


class AbstractPurchasedStuff(models.Model):
    """
    This object ONLY allow update or delete by the creator
    Other user can't update or delete

    Case:
    Produk A disbumit Andi dan telah dibeli Budi, bagaimana mungkin
    Andi memodifikasi / membatalkan pembelian Budi
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='purchased_stuff')
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='purchased_stuff')
    stuff = models.OneToOneField('shopping.Stuff', on_delete=models.CASCADE,
                                    related_name='purchased_stuff')
    purchased = models.ForeignKey('shopping.Purchased', on_delete=models.CASCADE,
                                  related_name='purchased_stuff')

    name = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.CharField(max_length=255)
    metric = models.CharField(max_length=15, choices=METRIC_CHOICES, default=None)
    # price divided by amount and quantity
    # eg: amount 6000 / quantity 6 = 1000
    price = models.BigIntegerField(default=0)
    amount = models.BigIntegerField(default=0)
    note = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    # True = item available, False = item un-available, None = no action
    is_found = models.BooleanField(default=None, null=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Purchased Stuff")
        verbose_name_plural = _("Purchased Stuffs")

    def __str__(self):
        if self.name:
            return self.name
        return self.stuff.name

    def check_can_add(self):
        """ Jika current user bukan creator Basket cek boleh membeli atau tidak """
        if self.basket.user.uuid != self.current_user.uuid:
            is_can_buy = self.share.filter(is_can_buy=True).exists()
            if not self.share.exists() or not is_can_buy:
                raise ValidationError({'detail': _("Tidak diizinkan melakukan pembelian di {}".format(self.basket.name))})
    
    def check_can_update(self):
        """ 
        Jika current user bukan creator maka tidak boleh update 
        Jika belanja is_complete = True tidak bisa diupdate
        Kecuali jika stuff is_additional = True
        """

        if self.user.uuid != self.current_user.uuid:
            is_can_buy = self.share.filter(is_can_buy=True).exists()
            if not self.share.exists() or not is_can_buy:
                raise ValidationError({'detail': _("Tidak diizinkan merubah {}".format(self.stuff.name))})
        
        if self.basket.is_complete and not self.stuff.is_additional and self.is_found:
            raise ValidationError({'detail': _("Merubah pembelian {} tidak diperbolehkan".format(self.stuff.name))})
    
    def check_can_delete(self):
        """ Hanya bisa dihapus oleh creator """
        if self.user.uuid != self.current_user.uuid:
            raise ValidationError("Tidak diizinkan menghapus {}".format(self.stuff.name))
        
        if self.basket.is_complete and not self.stuff.is_additional:
            raise ValidationError(_("Menghapus pembelian {} tidak diperbolehkan".format(self.stuff.name)))

    def clean(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request:
            self.current_user = self.request.user
            self.share = self.basket.share.filter(to_user_id=self.current_user.id)

            if self.pk:
                self.check_can_update()
            else:
                self.check_can_add()
        return super().clean()

    def save(self, *args, **kwargs):
        if self.metric != NOMINAL and self.amount > 0:
            qty = 1

            if isinstance(self.quantity, int):
                qty = int(self.quantity)
            
            if isinstance(self.quantity, float):
                qty = float(self.quantity)
    
            self.price = self.amount / qty
        else:
            self.price = self.amount

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request is not None:
            self.current_user = self.request.user
            self.check_can_delete()

        super().delete(*args, **kwargs)

    @property
    def to_user(self):
        return self.purchased.to_user


class AbstractTrackLocation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    purchased = models.ForeignKey('shopping.Purchased', on_delete=models.CASCADE,
                                  related_name='track_location')

    name = models.TextField(null=True, blank=True)
    latitude = models.CharField(max_length=255)
    longitude = models.CharField(max_length=255)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Track Location")
        verbose_name_plural = _("Track Locations")

    def __str__(self):
        return self.name
