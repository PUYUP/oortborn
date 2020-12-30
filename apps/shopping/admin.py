from django.contrib import admin
from django.contrib.auth import get_user_model

from utils.generals import get_model

Brand = get_model('shopping', 'Brand')
Product = get_model('shopping', 'Product')
ProductRate = get_model('shopping', 'ProductRate')
ProductAttachment = get_model('shopping', 'ProductAttachment')
Basket = get_model('shopping', 'Basket')
BasketAttachment = get_model('shopping', 'BasketAttachment')
Stuff = get_model('shopping', 'Stuff')
StuffAttachment = get_model('shopping', 'StuffAttachment')
Schedule = get_model('shopping', 'Schedule')
Share = get_model('shopping', 'Share')
Purchased = get_model('shopping', 'Purchased')
PurchasedStuff = get_model('shopping', 'PurchasedStuff')
Circle = get_model('shopping', 'Circle')
CircleMember = get_model('shopping', 'CircleMember')


class ShareExtend(admin.ModelAdmin):
    model = Share

    def get_queryset(self, request):
        qs = super().get_queryset(request) \
            .prefetch_related('user', 'basket', 'circle', 'to_user') \
            .select_related('user', 'basket', 'circle', 'to_user')

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'basket':
            kwargs['queryset'] = Basket.objects \
                .prefetch_related('user', 'completed_by') \
                .select_related('user', 'completed_by')
        
        if db_field.name == 'circle':
            kwargs['queryset'] = Circle.objects \
                .prefetch_related('user') \
                .select_related('user')

        if db_field.name == 'user':
            kwargs['queryset'] = get_user_model().objects \
                .prefetch_related('account', 'profile') \
                .select_related('account', 'profile')

        if db_field.name == 'to_user':
            kwargs['queryset'] = get_user_model().objects \
                .prefetch_related('account', 'profile') \
                .select_related('account', 'profile')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PurchasedExtend(admin.ModelAdmin):
    model = Purchased

    def get_queryset(self, request):
        qs = super().get_queryset(request) \
            .prefetch_related('user', 'basket', 'schedule') \
            .select_related('user', 'basket', 'schedule')

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'basket':
            kwargs['queryset'] = Basket.objects \
                .prefetch_related('user', 'completed_by') \
                .select_related('user', 'completed_by')
        
        if db_field.name == 'user':
            kwargs['queryset'] = get_user_model().objects \
                .prefetch_related('account', 'profile') \
                .select_related('account', 'profile')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PurchasedStuffExtend(admin.ModelAdmin):
    model = PurchasedStuff

    def get_queryset(self, request):
        qs = super().get_queryset(request) \
            .prefetch_related('user', 'basket', 'stuff', 'purchased') \
            .select_related('user', 'basket', 'stuff', 'purchased')

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'basket':
            kwargs['queryset'] = Basket.objects \
                .prefetch_related('user', 'completed_by') \
                .select_related('user', 'completed_by')

        if db_field.name == 'stuff':
            kwargs['queryset'] = Stuff.objects \
                .prefetch_related('user', 'basket', 'product', 'purchased_stuff') \
                .select_related('user', 'basket', 'product', 'purchased_stuff')
        
        if db_field.name == 'purchased':
            kwargs['queryset'] = Purchased.objects \
                .prefetch_related('user', 'basket', 'schedule') \
                .select_related('user', 'basket', 'schedule')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductRate)
admin.site.register(ProductAttachment)
admin.site.register(Basket)
admin.site.register(BasketAttachment)
admin.site.register(Stuff)
admin.site.register(StuffAttachment)
admin.site.register(Schedule)
admin.site.register(Share, ShareExtend)
admin.site.register(Purchased, PurchasedExtend)
admin.site.register(PurchasedStuff, PurchasedStuffExtend)
admin.site.register(Circle)
admin.site.register(CircleMember)
