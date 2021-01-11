from django.apps import AppConfig
from django.db.models.signals import post_save, pre_save, post_delete


class ShoppingConfig(AppConfig):
    name = 'apps.shopping'

    def ready(self):
        from utils.generals import get_model
        from .signals import (
            purchased_save_handler, 
            purchased_delete_handler,
            purchased_stuff_save_handler, 
            share_delete_handler,
            purchased_stuff_delete_handler,
            order_save_handler,
            order_delete_handler,
            order_line_save_handler
        )

        Purchased = get_model('shopping', 'Purchased')
        PurchasedStuff = get_model('shopping', 'PurchasedStuff')
        Share = get_model('shopping', 'Share')
        Order = get_model('shopping', 'Order')
        OrderLine = get_model('shopping', 'OrderLine')

        post_save.connect(purchased_save_handler, sender=Purchased,
                          dispatch_uid='purchased_save_signal')
        post_save.connect(purchased_stuff_save_handler, sender=PurchasedStuff,
                          dispatch_uid='purchased_stuff_save_signal')
        post_save.connect(order_save_handler, sender=Order,
                          dispatch_uid='order_save_signal')
        post_save.connect(order_line_save_handler, sender=OrderLine,
                          dispatch_uid='order_line_save_signal')

        post_delete.connect(share_delete_handler, sender=Share,
                            dispatch_uid='share_delete_signal')
        post_delete.connect(purchased_stuff_delete_handler, sender=PurchasedStuff,
                            dispatch_uid='purchased_stuff_delete_signal')
        post_delete.connect(order_delete_handler, sender=Order,
                            dispatch_uid='order_delete_signal')
        post_delete.connect(purchased_delete_handler, sender=Purchased,
                            dispatch_uid='purchased_delete_signal')
