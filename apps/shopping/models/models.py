from .master import *
from .basket import *
from .purchased import *
from .circle import *
from .order import *
from .invoice import *
from .assign import *
from .shipping import *

from utils.generals import is_model_registered

__all__ = list()


# 1
if not is_model_registered('shopping', 'Category'):
    class Category(AbstractCategory):
        class Meta(AbstractCategory.Meta):
            db_table = 'shopping_category'

    __all__.append('Category')


# 2
if not is_model_registered('shopping', 'Brand'):
    class Brand(AbstractBrand):
        class Meta(AbstractBrand.Meta):
            db_table = 'shopping_brand'

    __all__.append('Brand')


# 3
if not is_model_registered('shopping', 'Product'):
    class Product(AbstractProduct):
        class Meta(AbstractProduct.Meta):
            db_table = 'shopping_product'

    __all__.append('Product')


# 4
if not is_model_registered('shopping', 'ProductMetric'):
    class ProductMetric(AbstractProductMetric):
        class Meta(AbstractProductMetric.Meta):
            db_table = 'shopping_product_metric'

    __all__.append('ProductMetric')


# 5
if not is_model_registered('shopping', 'ProductRate'):
    class ProductRate(AbstractProductRate):
        class Meta(AbstractProductRate.Meta):
            db_table = 'shopping_product_rate'

    __all__.append('ProductRate')


# 6
if not is_model_registered('shopping', 'ProductAttachment'):
    class ProductAttachment(AbstractProductAttachment):
        class Meta(AbstractProductAttachment.Meta):
            db_table = 'shopping_product_attachment'

    __all__.append('ProductAttachment')


# 7
if not is_model_registered('shopping', 'Basket'):
    class Basket(AbstractBasket):
        class Meta(AbstractBasket.Meta):
            db_table = 'shopping_basket'

    __all__.append('Basket')


# 8
if not is_model_registered('shopping', 'BasketAttachment'):
    class BasketAttachment(AbstractBasketAttachment):
        class Meta(AbstractBasketAttachment.Meta):
            db_table = 'shopping_basket_attachment'

    __all__.append('BasketAttachment')


# 9
if not is_model_registered('shopping', 'Stuff'):
    class Stuff(AbstractStuff):
        class Meta(AbstractStuff.Meta):
            db_table = 'shopping_stuff'

    __all__.append('Stuff')


# 10
if not is_model_registered('shopping', 'StuffAttachment'):
    class StuffAttachment(AbstractStuffAttachment):
        class Meta(AbstractStuffAttachment.Meta):
            db_table = 'shopping_stuff_attachment'

    __all__.append('StuffAttachment')


# 11
if not is_model_registered('shopping', 'Share'):
    class Share(AbstractShare):
        class Meta(AbstractShare.Meta):
            db_table = 'shopping_share'

    __all__.append('Share')


# 12
if not is_model_registered('shopping', 'Purchased'):
    class Purchased(AbstractPurchased):
        class Meta(AbstractPurchased.Meta):
            db_table = 'shopping_purchased'

    __all__.append('Purchased')


# 13
if not is_model_registered('shopping', 'PurchasedStuff'):
    class PurchasedStuff(AbstractPurchasedStuff):
        class Meta(AbstractPurchasedStuff.Meta):
            db_table = 'shopping_purchased_stuff'

    __all__.append('PurchasedStuff')


# 14
if not is_model_registered('shopping', 'PurchasedStuffAttachment'):
    class PurchasedStuffAttachment(AbstractPurchasedStuffAttachment):
        class Meta(AbstractPurchasedStuffAttachment.Meta):
            db_table = 'shopping_purchased_stuff_attachment'

    __all__.append('PurchasedStuffAttachment')


# 15
if not is_model_registered('shopping', 'Schedule'):
    class Schedule(AbstractSchedule):
        class Meta(AbstractSchedule.Meta):
            db_table = 'shopping_schedule'

    __all__.append('Schedule')


# 16
if not is_model_registered('shopping', 'Circle'):
    class Circle(AbstractCircle):
        class Meta(AbstractCircle.Meta):
            db_table = 'shopping_circle'

    __all__.append('Circle')


# 17
if not is_model_registered('shopping', 'CircleMember'):
    class CircleMember(AbstractCircleMember):
        class Meta(AbstractCircleMember.Meta):
            db_table = 'shopping_circle_member'

    __all__.append('CircleMember')


# 18
if not is_model_registered('shopping', 'Order'):
    class Order(AbstractOrder):
        class Meta(AbstractOrder.Meta):
            db_table = 'shopping_order'

    __all__.append('Order')


# 19
if not is_model_registered('shopping', 'OrderLine'):
    class OrderLine(AbstractOrderLine):
        class Meta(AbstractOrderLine.Meta):
            db_table = 'shopping_order_line'

    __all__.append('OrderLine')


# 20
if not is_model_registered('shopping', 'OrderSchedule'):
    class OrderSchedule(AbstractOrderSchedule):
        class Meta(AbstractOrderSchedule.Meta):
            db_table = 'shopping_order_schedule'

    __all__.append('OrderSchedule')


# 21
if not is_model_registered('shopping', 'OrderDelivery'):
    class OrderDelivery(AbstractOrderDelivery):
        class Meta(AbstractOrderDelivery.Meta):
            db_table = 'shopping_order_delivery'

    __all__.append('OrderDelivery')


# 22
if not is_model_registered('shopping', 'Invoice'):
    class Invoice(AbstractInvoice):
        class Meta(AbstractInvoice.Meta):
            db_table = 'shopping_invoice'

    __all__.append('Invoice')


# 23
if not is_model_registered('shopping', 'InvoiceLine'):
    class InvoiceLine(AbstractInvoiceLine):
        class Meta(AbstractInvoiceLine.Meta):
            db_table = 'shopping_invoice_line'

    __all__.append('InvoiceLine')


# 24
if not is_model_registered('shopping', 'ShippingAddress'):
    class ShippingAddress(AbstractShippingAddress):
        class Meta(AbstractShippingAddress.Meta):
            db_table = 'shopping_shipping_address'

    __all__.append('ShippingAddress')


# 25
if not is_model_registered('shopping', 'ShippingMethod'):
    class ShippingMethod(AbstractShippingMethod):
        class Meta(AbstractShippingMethod.Meta):
            db_table = 'shopping_shipping_method'

    __all__.append('ShippingMethod')


# 26
if not is_model_registered('shopping', 'Assign'):
    class Assign(AbstractAssign):
        class Meta(AbstractAssign.Meta):
            db_table = 'shopping_assign'

    __all__.append('Assign')


# 27
if not is_model_registered('shopping', 'AssignTracking'):
    class AssignTracking(AbstractAssignTracking):
        class Meta(AbstractAssignTracking.Meta):
            db_table = 'shopping_assign_tracking'

    __all__.append('AssignTracking')


# 28
if not is_model_registered('shopping', 'AssignLog'):
    class AssignLog(AbstractAssignLog):
        class Meta(AbstractAssignLog.Meta):
            db_table = 'shopping_assign_log'

    __all__.append('AssignLog')
