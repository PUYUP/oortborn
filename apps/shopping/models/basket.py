import uuid
import os

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ..utils.constants import METRIC_CHOICES, GENERAL_STATUS, WAITING
from utils.validators import non_python_keyword, identifier_validator
from utils.generals import quantity_format
from utils.mixin.generals import ModelDiffMixin


class AbstractBasket(ModelDiffMixin, models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='basket_user', db_index=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='basket_completed_by', null=True, 
                                     blank=True, db_index=True)

    name = models.CharField(max_length=255, db_index=True)
    note = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    # general sort
    sort = models.IntegerField(default=1, db_index=True)
    # sort after complete
    complete_sort = models.IntegerField(default=1, db_index=True)
    complete_at = models.DateTimeField(auto_now=False, blank=True, null=True)

    is_complete = models.BooleanField(default=False, db_index=True)
    is_purchased = models.BooleanField(default=False, db_index=True)
    # True = send to assistant
    # False = buy self
    # Null = no action (fresh order)
    is_ordered = models.BooleanField(default=None, null=True, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Basket")
        verbose_name_plural = _("Baskets")

    def __str__(self):
        return self.name

    @property
    def is_order_ongoing(self):
        if hasattr(self, 'order'):
            return self.order.is_ongoing
        return False

    def check_can_update(self):
        """ 
        Hanya creator boleh mengedit 
        User lain dengan Share is_can_buy hanya boleh mengupdate field is_complete
        """
        if self.user.uuid != self.current_user.uuid:
            share = self.share.filter(to_user_id=self.current_user.id)
            is_can_buy = share.filter(is_can_buy=True)

            if not share.exists() or not is_can_buy:
                raise ValidationError({'detail': _("Tidak boleh merubah {}".format(self.name))})

    def check_can_delete(self):
        """ Hanya creatro boleh menghapus """
        if self.is_ordered:
            raise ValidationError(_("Sudah dikirim ke Asisten Belanja tidak bisa dihapus".format(self.name)))

        if self.user.uuid != self.current_user.uuid:
            raise ValidationError(_("Tidak boleh menghapus {}".format(self.name)))
        
    def clean(self, *args, **kwargs):
        self.source = kwargs.pop('source', None)
        if self.pk and self.is_ordered and self.source != 'sorting':
            raise ValidationError({'detail': _("Sudah dikirim ke Asisten Belanja tindakan ditolak".format(self.name))})

        self.request = kwargs.pop('request', None)
        if self.request is not None:
            self.current_user = self.request.user

            if self.pk:
                self.check_can_update()

        return super().clean()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request is not None:
            self.current_user = self.request.user
            self.check_can_delete()
    
        super().delete()


class AbstractBasketAttachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='basket_attachment')
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='basket_attachment', db_index=True)

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='files/basket-attachment/', max_length=500,
                            null=True, blank=True)
    image = models.FileField(upload_to='images/basket-attachment/', max_length=500,
                             null=True, blank=True)
    mime = models.CharField(max_length=225, editable=False, null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Basket Attachment")
        verbose_name_plural = _("Basket Attachments")

    def __str__(self):
        return self.name

    def check_can_add(self):
        """
        Jika current user bukan creator Basket
        Cek apakah user dibolehkan menambah Attachment
        Jika current user dalam Share is_can_crud maka boleh menambahkan
        """

        if self.basket.user.uuid != self.current_user.uuid:
            is_can_crud = self.share.filter(is_can_crud=True).exists()
            is_can_buy = self.share.filter(is_can_buy=True).exists()

            if (not self.share.exists() or not is_can_crud) or (self.basket.is_complete and not is_can_buy):
                raise ValidationError({'detail': _("Tidak boleh menambah lampiran dalam {}".format(self.basket.name))})
    
    def check_can_update(self):
        """
        Cek apakah user creator Attachment atau creator Basket
        Jika creator Basket boleh crud
        Jika Share is_admin boleh crud
        """

        if self.user.uuid != self.current_user.uuid and self.basket.user.uuid != self.current_user.uuid:
            is_admin = self.share.filter(is_admin=True).exists()
            if not is_admin:
                raise ValidationError({'detail': _("Merubah lampiran {} ditolak".format(self.name))})
    
    def check_can_delete(self):
        """
        tapi hanya berlaku jika yang beli bukan creator
        Jika current user bukan creator, cek Share is_admin baru boleh menghapus
        """
        if self.user.uuid != self.current_user.uuid:
            is_admin = self.share.filter(is_admin=True).exists()
            if not is_admin:
                raise ValidationError(_("Menghapus {} ditolak".format(self.name)))
        
    def clean(self, *args, **kwargs):
        if not self.file and not self.image:
            raise ValidationError({'detail': _("File or Image required")})
        
        self.request = kwargs.pop('request', None)
        if self.request is not None:
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
            self.share = self.basket.share.filter(to_user_id=self.current_user.id)
            self.check_can_delete()
    
        super().delete()

    def save(self, *args, **kwargs):
        ext = None

        if self.file:
            name, ext = os.path.splitext(self.file.name)

        if self.image:
            name, ext = os.path.splitext(self.image.name)
        
        if ext:
            self.mime = ext
        super().save(*args, **kwargs)


class AbstractStuff(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='stuff', db_index=True)
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='stuff', db_index=True)
    product = models.ForeignKey('shopping.Product', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='stuff')

    name = models.CharField(max_length=255, db_index=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    metric = models.CharField(max_length=15, choices=METRIC_CHOICES,
                              validators=[identifier_validator, non_python_keyword])
    note = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    sort = models.IntegerField(default=1, db_index=True)
    done_at = models.DateTimeField(auto_now=False, blank=True, null=True)
    is_done = models.BooleanField(default=False, db_index=True)
    # Basket has complete and user add more Stuff, so mark as additional
    is_additional = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Stuff")
        verbose_name_plural = _("Stuffs")

    def __str__(self):
        return self.name

    @property
    def get_purchased_stuff(self):
        if hasattr(self, 'purchased_stuff'):
            return self.purchased_stuff
        else:
            return None

    @property
    def quantity_format(self):
        if self.quantity:
            return quantity_format(quantity=self.quantity)
        return self.quantity
    
    def check_can_add(self):
        """
        Jika current user bukan creator Basket
        Cek apakah user dibolehkan menambah Stuff
        Jika current user dalam Share is_can_crud maka boleh menambahkan
        """

        if self.basket.user.uuid != self.current_user.uuid:
            is_can_crud = self.share.filter(is_can_crud=True).exists()
            is_can_buy = self.share.filter(is_can_buy=True).exists()

            if (not self.share.exists() or not is_can_crud) or (self.basket.is_complete and not is_can_buy):
                raise ValidationError({'detail': _("Tidak boleh menambah item dalam {}".format(self.basket.name))})

    def check_can_update(self):
        """
        Cek apakah user creator Stuff atau creator Basket
        Jika creator Basket boleh crud
        Jika Share is_admin boleh crud
        Namun hanya ketika Stuff belum purchased
        """

        if self.get_purchased_stuff is not None:
            raise ValidationError({'detail': _("{} sudah dibeli {} tidak bisa dirubah".format(self.name, self.purchased_stuff.user.first_name))})

        if self.user.uuid != self.current_user.uuid and self.basket.user.uuid != self.current_user.uuid:
            is_admin = self.share.filter(is_admin=True).exists()
            if not is_admin:
                raise ValidationError({'detail': _("Merubah {} ditolak".format(self.name))})
        
        if self.basket.is_complete and not self.is_additional:
            raise ValidationError({'detail': _("Merubah item {} setelah belanja selesai tidak boleh".format(self.name))})

    def check_can_delete(self):
        """
        Jika sudah Purchase tidak bisa dihapus sebelum PurchaseStuff dibatalkan (dihapus), 
        tapi hanya berlaku jika yang beli bukan creator
        Jika current user bukan creator, cek Share is_admin baru boleh menghapus
        """
        if self.basket.is_ordered:
            raise ValidationError(_("Sudah dikirim ke Asisten Belanja tidak bisa dihapus"))

        purchased_stuff = self.get_purchased_stuff
        if purchased_stuff is not None:
            if purchased_stuff.user.uuid != self.current_user.uuid:
                raise ValidationError(_("{} sudah dibeli {} tidak bisa dihapus".format(self.name, purchased_stuff.user.first_name)))

        if self.user.uuid != self.current_user.uuid:
            is_admin = self.share.filter(is_admin=True).exists()
            if not is_admin:
                raise ValidationError(_("Menghapus {} ditolak".format(self.name)))

        if self.basket.is_complete and not self.is_additional:
            raise ValidationError(_("Menghapus item {} setelah belanja selesai tidak diperbolehkan".format(self.name)))

    def clean(self, *args, **kwargs):
        self.source = kwargs.pop('source', None)
        if self.pk and self.basket.is_ordered and self.source != 'sorting':
            raise ValidationError({'detail': _("Sudah dikirim ke Asisten Belanja tindakan ditolak".format(self.name))})

        self.request = kwargs.pop('request', None)
        if self.request is not None:
            self.current_user = self.request.user

            if hasattr(self, 'basket'):
                self.share = self.basket.share.filter(to_user_id=self.current_user.id)

                if self.pk:
                    self.check_can_update()
                else:
                    self.check_can_add()
        
        # Quantity can't zero or lower
        if self.quantity <= 0:
            raise ValidationError({'quantity': _("Jumlah tidak boleh kurang dari nol")})
        return super().clean()

    def save(self, *args, **kwargs):
        if self.basket.is_complete:
            self.is_additional = True

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request is not None:
            self.current_user = self.request.user
            self.share = self.basket.share.filter(to_user_id=self.current_user.id)
            self.check_can_delete()
    
        super().delete()

    @property
    def is_found(self):
        if hasattr(self, 'purchased_stuff'):
            return self.purchased_stuff.is_found
        else:
            return None


class AbstractStuffAttachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='stuff_attachment')
    stuff = models.ForeignKey('shopping.Stuff', on_delete=models.CASCADE,
                              related_name='stuff_attachment', db_index=True)

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='files/stuff-attachment/', max_length=500,
                            null=True, blank=True)
    image = models.FileField(upload_to='images/stuff-attachment/', max_length=500,
                             null=True, blank=True)
    mime = models.CharField(max_length=225)
    sort = models.IntegerField(default=1)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Stuff Attachment")
        verbose_name_plural = _("Stuff Attachments")

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


class AbstractShare(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='share_user', db_index=True)
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='share', db_index=True)
    circle = models.ForeignKey('shopping.Circle', on_delete=models.CASCADE,
                               related_name='share', null=True, blank=True)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='share_to_user', db_index=True)
    
    status = models.CharField(choices=GENERAL_STATUS, default=WAITING, max_length=15,
                              validators=[identifier_validator, non_python_keyword])
    sort = models.IntegerField(default=1)
    # all crud allowed (for stuff and basket)
    is_admin = models.BooleanField(default=False)
    # only stuff created by him self
    is_can_crud = models.BooleanField(default=False)
    is_can_buy = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Share")
        verbose_name_plural = _("Shares")

    def __str__(self):
        return self.to_user.username
    
    def check_can_add(self):
        """ Hanya creator Basket yg bisa membagikan """
        if self.basket.user.uuid != self.current_user.uuid:
            raise ValidationError({'detail': _("Hanya pemilik yang boleh membagikan {}".format(self.basket.name))})

    def check_can_update(self):
        """ 
        Hanya creator Basket yg bisa merubah 
        Atau jika user dibagikan dengan status = 'waiting'
        """
        if (self.share_obj and self.share_obj.status != 'waiting' and self.source != 'sorting') and (self.user.uuid != self.current_user.uuid):
            raise ValidationError({'detail': _("Tidak bisa merubah")})

    def check_can_delete(self):
        """ 
        Hanya bisa dihapus oleh creator 
        Hanya jika belanja belum selesai
        Hanya jika to_user belum berkontribusi
        """

        if not self.share.exists() and self.user.uuid != self.current_user.uuid:
            raise ValidationError(_("Tidak diizinkan menghapus"))
    
        to_user_has_stuff = self.basket.stuff.filter(user_id=self.to_user.id).exists()
        to_user_has_purchased = self.basket.purchased_stuff.filter(user_id=self.to_user.id).exists()

        if to_user_has_stuff or to_user_has_purchased:
            if self.to_user.id != self.current_user.id:
                raise ValidationError(_("{} sudah menambahkan / membeli item. Tidak bisa dihapus".format(self.to_user.first_name)))
            raise ValidationError(_("Anda memiliki item di {}. Tidak bisa dihapus. Hapus terlebih dahulu item Anda untuk menghapus daftar ini.".format(self.basket.name)))

    def clean(self, *args, **kwargs):
        self.source = kwargs.pop('source', None)
        self.request = kwargs.pop('request', None)

        if self.request is not None:
            self.current_user = self.request.user
            self.share = self.basket.share.filter(to_user_id=self.current_user.id)
            self.share_obj = self.share.get() if self.share.exists() else None
    
            if self.pk:
                self.check_can_update()
            else:
                self.check_can_add()

        # Can't share to him self
        if self.basket.user.id == self.to_user.id:
            raise ValidationError({'to_user': _("Tidak boleh membagikan ke akun sendiri")})
        
        return super().clean()

    def save(self, *args, **kwargs):
        if self.is_admin:
            self.is_can_crud = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request is not None:
            self.current_user = self.request.user
            self.share = self.basket.share.filter(to_user_id=self.current_user.id)
            self.check_can_delete()
    
        super().delete()

    @property
    def basket_owner(self):
        return self.to_user.username


class AbstractSchedule(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='schedule')
    basket = models.ForeignKey('shopping.Basket', on_delete=models.CASCADE,
                               related_name='schedule', db_index=True)

    datetime = models.DateTimeField(auto_now=False, db_index=True)
    is_remind = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True
        app_label = 'shopping'
        ordering = ['-create_at']
        verbose_name = _("Schedule")
        verbose_name_plural = _("Schedules")

    def __str__(self):
        return self.datetime
