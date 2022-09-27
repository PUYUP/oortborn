from django.contrib import admin
from django.contrib.auth import get_user_model

from utils.generals import get_model

Category = get_model('shopping', 'Category')
Brand = get_model('shopping', 'Brand')
Product = get_model('shopping', 'Product')
ProductMetric = get_model('shopping', 'ProductMetric')
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

Order = get_model('shopping', 'Order')
OrderLine = get_model('shopping', 'OrderLine')
OrderSchedule = get_model('shopping', 'OrderSchedule')
OrderDelivery = get_model('shopping', 'OrderDelivery')
Invoice = get_model('shopping', 'Invoice')
InvoiceLine = get_model('shopping', 'InvoiceLine')
ShippingAddress = get_model('shopping', 'ShippingAddress')
ShippingMethod = get_model('shopping', 'ShippingMethod')
Assign = get_model('shopping', 'Assign')
AssignTracking = get_model('shopping', 'AssignTracking')
AssignLog = get_model('shopping', 'AssignLog')


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


class ProductRateInline(admin.StackedInline):
    model = ProductRate
    ordering = ['-create_at']
    max_num = 3

    def get_queryset(self, request):
        qs = super().get_queryset(request) \
            .prefetch_related('user', 'product', 'purchased_stuff') \
            .select_related('user', 'product', 'purchased_stuff')

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = get_user_model().objects \
                .prefetch_related('account', 'profile') \
                .select_related('account', 'profile')

        if db_field.name == 'purchased_stuff':
            kwargs['queryset'] = PurchasedStuff.objects \
                .prefetch_related('user', 'basket', 'stuff', 'purchased') \
                .select_related('user', 'basket', 'stuff', 'purchased')

        if db_field.name == 'product':
            kwargs['queryset'] = Product.objects \
                .prefetch_related('user', 'brand') \
                .select_related('user', 'brand')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProductAttachmentInline(admin.StackedInline):
    model = ProductAttachment
    ordering = ['-create_at']
    max_num = 3


class ProductMetricInline(admin.StackedInline):
    model = ProductMetric
    ordering = ['-create_at']


class ProductExtend(admin.ModelAdmin):
    model = Product
    inlines = [ProductMetricInline, ProductRateInline, ProductAttachmentInline,]
    search_fields = ['name',]

    def get_queryset(self, request):
        qs = super().get_queryset(request) \
            .prefetch_related('user', 'product_rate', 'product_metric') \
            .select_related('user')

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = get_user_model().objects \
                .prefetch_related('account', 'profile') \
                .select_related('account', 'profile')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProductRateExtend(admin.ModelAdmin):
    model = ProductRate

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = get_user_model().objects \
                .prefetch_related('account', 'profile') \
                .select_related('account', 'profile')

        if db_field.name == 'purchased_stuff':
            kwargs['queryset'] = PurchasedStuff.objects \
                .prefetch_related('user', 'basket', 'stuff', 'purchased') \
                .select_related('user', 'basket', 'stuff', 'purchased')

        if db_field.name == 'product':
            kwargs['queryset'] = Product.objects \
                .prefetch_related('user', 'brand', 'category') \
                .select_related('user', 'brand', 'category')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AssignInline(admin.StackedInline):
    model = Assign


class OrderExtend(admin.ModelAdmin):
    model = Product
    inlines = [AssignInline,]
    readonly_fields = ['customer',]


admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product, ProductExtend)
admin.site.register(ProductMetric)
admin.site.register(ProductRate, ProductRateExtend)
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

admin.site.register(Order, OrderExtend)
admin.site.register(OrderLine)
admin.site.register(OrderSchedule)
admin.site.register(OrderDelivery)
admin.site.register(Invoice)
admin.site.register(InvoiceLine)
admin.site.register(ShippingAddress)
admin.site.register(ShippingMethod)
admin.site.register(Assign)
admin.site.register(AssignTracking)
admin.site.register(AssignLog)
