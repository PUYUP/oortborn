from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class ShoppingConfig(AppConfig):
    name = 'apps.shopping'

    def ready(self):
        from utils.generals import get_model
        from .signals import (
            purchased_save_handler, 
            purchased_stuff_save_handler, 
            stuff_save_handler,
            share_delete_handler,
            purchased_stuff_delete_handler
        )

        Purchased = get_model('shopping', 'Purchased')
        PurchasedStuff = get_model('shopping', 'PurchasedStuff')
        Stuff = get_model('shopping', 'Stuff')
        Share = get_model('shopping', 'Share')

        post_save.connect(purchased_save_handler, sender=Purchased,
                          dispatch_uid='purchased_save_signal')
        post_save.connect(purchased_stuff_save_handler, sender=PurchasedStuff,
                          dispatch_uid='purchased_stuff_save_signal')
        post_save.connect(stuff_save_handler, sender=Stuff,
                          dispatch_uid='stuff_save_signal')
        
        post_delete.connect(share_delete_handler, sender=Share,
                            dispatch_uid='share_delete_signal')
        post_delete.connect(purchased_stuff_delete_handler, sender=PurchasedStuff,
                            dispatch_uid='purchased_stuff_delete_signal')
    
