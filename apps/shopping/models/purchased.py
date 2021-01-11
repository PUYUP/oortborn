from utils.generals import quantity_format
import uuid
import os

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ..utils.constants import METRIC_CHOICES, NOMINAL
from utils.validators import non_python_keyword, identifier_validator


class AbstractPurchased(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='purchased', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='purchased_user', db_index=True)
    schedule = models.ForeignKey('shopping.Schedule', on_delete=models.SET_NULL,
                                 related_name='purchased', null=True, blank=True, 
                                 db_index=True)

    started_at = models.DateTimeField(auto_now=False, blank=True, null=True, db_index=True)
    complete_at = models.DateTimeField(auto_now=False, blank=True, null=True, db_index=True)
    is_ongoing = models.BooleanField(default=True, db_index=True)
    is_complete = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Purchased")
        verbose_name_plural = _("Purchaseds")

    def __str__(self):
        return self.basket.name
    
    def check_can_add(self):
        """ 
        Jika current user bukan creator Basket cek boleh membeli atau tidak 
        Jika Basket sudah dikirim ke operator maka pembelian sendiri tidak diperbolehkan
        """
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
        
        if self.basket.is_ordered:
            raise ValidationError({'detail': _("Sudah dikirim ke Asisten Belanja tidak bisa dihapus")})

    def clean(self, *args, **kwargs):
        if self.pk and self.basket.is_ordered:
            raise ValidationError({'detail': _("Sudah dikirim ke Asisten Belanja tindakan ditolak")})

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

        super().delete()


class AbstractPurchasedStuff(models.Model):
    """
    This object ONLY allow update or delete by the creator
    Other user can't update or delete

    Case:
    Produk A disbumit Andi dan telah dibeli Budi, bagaimana mungkin
    Andi memodifikasi / membatalkan pembelian Budi
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='purchased_stuff', db_index=True)
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='purchased_stuff', db_index=True)
    stuff = models.OneToOneField('shopping.Stuff', on_delete=models.CASCADE,
                                 related_name='purchased_stuff', db_index=True)
    purchased = models.ForeignKey('shopping.Purchased', on_delete=models.CASCADE,
                                  related_name='purchased_stuff', db_index=True)

    name = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    metric = models.CharField(max_length=15, choices=METRIC_CHOICES, default=None,
                              validators=[identifier_validator, non_python_keyword])
    # price divided by amount and quantity
    # eg: amount 6000 / quantity 6 = 1000
    price = models.BigIntegerField(default=0)
    amount = models.BigIntegerField(default=0)
    note = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    # True = item available, False = item un-available, None = no action
    is_found = models.BooleanField(default=None, null=True, db_index=True)
    is_private = models.BooleanField(default=False, null=True, db_index=True)

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

    @property
    def quantity_format(self):
        if self.quantity:
            return quantity_format(quantity=self.quantity)
        return self.quantity

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        
        # save original values, when model is loaded from database,
        # in a separate attribute on the model
        instance._loaded_values = dict(zip(field_names, values))
        
        return instance

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

        # ambil is_found lama (dari database)
        original_is_found = None
        if not self._state.adding:
            original_is_found = self._loaded_values.get('is_found')

        if self.user.uuid != self.current_user.uuid:
            is_can_buy = self.share.filter(is_can_buy=True).exists()
            if not self.share.exists() or not is_can_buy:
                raise ValidationError({'detail': _("Tidak diizinkan merubah {}".format(self.stuff.name))})
        
        # jika state asli original_is_found is True maka tidak bisa edit
        if self.basket.is_complete and not self.stuff.is_additional and original_is_found:
            raise ValidationError({'detail': _("Merubah pembelian {} tidak diperbolehkan".format(self.stuff.name))})
    
    def check_can_delete(self):
        """ Hanya bisa dihapus oleh creator """
        if self.user.uuid != self.current_user.uuid:
            raise ValidationError("Tidak diizinkan menghapus {}".format(self.stuff.name))
        
        if self.basket.is_complete and not self.stuff.is_additional:
            raise ValidationError(_("Menghapus pembelian {} tidak diperbolehkan".format(self.stuff.name)))

    def clean(self, *args, **kwargs):
        if self.pk and self.basket.is_ordered:
            raise ValidationError({'detail': _("Sudah dikirim ke Asisten Belanja tindakan ditolak")})

        self.request = kwargs.pop('request', None)
        if self.request:
            self.current_user = self.request.user
            self.share = self.basket.share.filter(to_user_id=self.current_user.id)
            
            if self.pk:
                self.check_can_update()
            else:
                self.check_can_add()

        # Validation
        if self.is_found:
            if self.quantity <= 0:
                raise ValidationError({'quantity': _("Jumlah tidak boleh kurang dari nol")})

            # Jika belum purchased masih boleh nol
            # jika sudah purchased tidak boleh nol atau kurang
            if self.request and self.pk:
                if self.amount <= 0:
                    raise ValidationError({'amount': _("Total harga tidak boleh kurang dari nol")})

        return super().clean()

    def save(self, *args, **kwargs):
        if self.metric != NOMINAL and self.amount > 0 and self.quantity > 0:
            self.price = self.amount / self.quantity
        else:
            self.price = self.amount
        
        # Set price and amount to 0 if not found
        if not self.is_found:
            self.price = 0
            self.amount = 0

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request is not None:
            self.current_user = self.request.user
            self.check_can_delete()

        super().delete()


class AbstractPurchasedStuffAttachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='purchased_stuff_attachment')
    purchased = models.ForeignKey('shopping.Purchased', on_delete=models.CASCADE,
                                  related_name='purchased_stuff_attachment', db_index=True)

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='files/purchased-stuff-attachment/', max_length=500,
                            null=True, blank=True)
    image = models.FileField(upload_to='images/purchased-stuff-attachment/', max_length=500,
                             null=True, blank=True)
    mime = models.CharField(max_length=225)
    sort = models.IntegerField(default=1)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Purchased Stuff Attachment")
        verbose_name_plural = _("Purchased Stuff Attachments")

    def __str__(self):
        return self.name
    
    def clean(self, *args, **kwargs):
        return super().clean()

    def save(self, *args, **kwargs):
        ext = None
        if self.file:
            name, ext = os.path.splitext(self.file.name)

        if self.image:
            name, ext = os.path.splitext(self.image.name)
        
        if ext:
            self.mime = ext
        super().save(*args, **kwargs)
