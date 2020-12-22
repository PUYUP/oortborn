from .master import *
from .basket import *
from .purchased import *
from .circle import *

from utils.generals import is_model_registered

__all__ = list()


# 1
if not is_model_registered('shopping', 'Brand'):
    class Brand(AbstractBrand):
        class Meta(AbstractBrand.Meta):
            db_table = 'shopping_brand'

    __all__.append('Brand')


# 2
if not is_model_registered('shopping', 'Product'):
    class Product(AbstractProduct):
        class Meta(AbstractProduct.Meta):
            db_table = 'shopping_product'

    __all__.append('Product')


# 3
if not is_model_registered('shopping', 'ProductRate'):
    class ProductRate(AbstractProductRate):
        class Meta(AbstractProductRate.Meta):
            db_table = 'shopping_product_rate'

    __all__.append('ProductRate')


# 4
if not is_model_registered('shopping', 'ProductAttachment'):
    class ProductAttachment(AbstractProductAttachment):
        class Meta(AbstractProductAttachment.Meta):
            db_table = 'shopping_product_attachment'

    __all__.append('ProductAttachment')


# 5
if not is_model_registered('shopping', 'Basket'):
    class Basket(AbstractBasket):
        class Meta(AbstractBasket.Meta):
            db_table = 'shopping_basket'

    __all__.append('Basket')


# 6
if not is_model_registered('shopping', 'BasketAttachment'):
    class BasketAttachment(AbstractBasketAttachment):
        class Meta(AbstractBasketAttachment.Meta):
            db_table = 'shopping_basket_attachment'

    __all__.append('BasketAttachment')


# 7
if not is_model_registered('shopping', 'Stuff'):
    class Stuff(AbstractStuff):
        class Meta(AbstractStuff.Meta):
            db_table = 'shopping_stuff'

    __all__.append('Stuff')


# 8
if not is_model_registered('shopping', 'StuffAttachment'):
    class StuffAttachment(AbstractStuffAttachment):
        class Meta(AbstractStuffAttachment.Meta):
            db_table = 'shopping_stuff_attachment'

    __all__.append('StuffAttachment')


# 9
if not is_model_registered('shopping', 'Share'):
    class Share(AbstractShare):
        class Meta(AbstractShare.Meta):
            db_table = 'shopping_share'

    __all__.append('Share')


# 10
if not is_model_registered('shopping', 'Purchased'):
    class Purchased(AbstractPurchased):
        class Meta(AbstractPurchased.Meta):
            db_table = 'shopping_purchased'

    __all__.append('Purchased')


# 11
if not is_model_registered('shopping', 'PurchasedStuff'):
    class PurchasedStuff(AbstractPurchasedStuff):
        class Meta(AbstractPurchasedStuff.Meta):
            db_table = 'shopping_purchased_stuff'

    __all__.append('PurchasedStuff')


# 12
if not is_model_registered('shopping', 'TrackLocation'):
    class TrackLocation(AbstractTrackLocation):
        class Meta(AbstractTrackLocation.Meta):
            db_table = 'shopping_track_location'

    __all__.append('TrackLocation')


# 13
if not is_model_registered('shopping', 'Schedule'):
    class Schedule(AbstractSchedule):
        class Meta(AbstractSchedule.Meta):
            db_table = 'shopping_schedule'

    __all__.append('Schedule')


# 14
if not is_model_registered('shopping', 'Circle'):
    class Circle(AbstractCircle):
        class Meta(AbstractCircle.Meta):
            db_table = 'shopping_circle'

    __all__.append('Circle')


# 15
if not is_model_registered('shopping', 'CircleMember'):
    class CircleMember(AbstractCircleMember):
        class Meta(AbstractCircleMember.Meta):
            db_table = 'shopping_circle_member'

    __all__.append('CircleMember')
