from django.contrib import admin

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
TrackLocation = get_model('shopping', 'TrackLocation')
Circle = get_model('shopping', 'Circle')
CircleMember = get_model('shopping', 'CircleMember')

admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductRate)
admin.site.register(ProductAttachment)
admin.site.register(Basket)
admin.site.register(BasketAttachment)
admin.site.register(Stuff)
admin.site.register(StuffAttachment)
admin.site.register(Schedule)
admin.site.register(Share)
admin.site.register(Purchased)
admin.site.register(PurchasedStuff)
admin.site.register(TrackLocation)
admin.site.register(Circle)
admin.site.register(CircleMember)
