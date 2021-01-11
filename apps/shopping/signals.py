from django.db import transaction
from utils.generals import get_model

Purchased = get_model('shopping', 'Purchased')
Product = get_model('shopping', 'Product')
ProductRate = get_model('shopping', 'ProductRate')
OrderLine = get_model('shopping', 'OrderLine')


@transaction.atomic
def share_delete_handler(sender, instance, using, **kwargs):
    stuff_objs = instance.basket.stuff.filter(user_id=instance.to_user.id)
    purchased_objs = instance.basket.purchased.filter(user_id=instance.to_user.id)

    if stuff_objs.exists():
        stuff_objs.delete()

    if purchased_objs.exists():
        purchased_objs.delete()


@transaction.atomic
def stuff_save_handler(sender, instance, created, **kwargs):
    if not instance.product:
        _product, _created = Product.objects \
            .get_or_create(name=instance.name, defaults={'user': instance.user})


@transaction.atomic
def purchased_save_handler(sender, instance, created, **kwargs):
    if created:
        basket = getattr(instance, 'basket')
        basket.is_purchased = True
        basket.save()


@transaction.atomic
def purchased_delete_handler(sender, instance, using, **kwargs):
    basket = instance.basket
    if not basket.purchased.exists():
        basket.is_purchased = False
        basket.save()


@transaction.atomic
def purchased_stuff_save_handler(sender, instance, created, **kwargs):
    basket = instance.basket
    stuff = instance.stuff

    if created:
        purchased = instance.purchased
        purchased_user = purchased.user
        basket_user = basket.user
    
        # If basket creator and purchased user same, mark stuff is_done!
        # Ini akan digunakan untuk fitur assistant dimana customer mengecek
        # apakah semua item sudah terbeli dengan menandai sebagai 'is_done'
        if basket_user.id == purchased_user.id:
            stuff.is_done = True
        
        # Mark stuff purchased
        stuff.is_purchased = True
        stuff.save()

        # Collect product rate
        product_rate, _created = ProductRate.objects \
            .get_or_create(name=stuff.name, location=instance.location,
                           price=instance.price, quantity=instance.quantity,
                           metric=instance.metric, user=basket_user,
                           purchased_stuff=instance, is_private=instance.is_private,
                           product=instance.stuff.product)
    else:
        original_is_found = None
        if not instance._state.adding:
            original_is_found = instance._loaded_values.get('is_found')

        if original_is_found == False and original_is_found != instance.is_found and basket.is_complete:
            stuff.is_additional = True
            stuff.save()

        product_rate = getattr(instance, 'product_rate').last()
        if product_rate:
            product_rate.price = instance.price
            product_rate.location = instance.location
            product_rate.is_private = instance.is_private
            product_rate.save()


@transaction.atomic
def purchased_stuff_delete_handler(sender, instance, using, **kwargs):
    # delete Stuff if Stuff is_additional
    if instance.stuff.is_additional:
        instance.stuff.delete()


@transaction.atomic
def order_save_handler(sender, instance, created, **kwargs):
    if created:
        # store all stuff as order item
        basket = instance.basket
        stuffs = basket.stuff.all()
        create_order_lines = []

        # set basket to ordered
        basket.is_ordered = True
        basket.save()

        for stuff in stuffs:
            order_line_obj = OrderLine(order=instance, customer=instance.customer, stuff=stuff,
                                       name=stuff.name, quantity=stuff.quantity, metric=stuff.metric,
                                       note=stuff.note, location=stuff.location)
            create_order_lines.append(order_line_obj)
    
        if len(create_order_lines) > 0:
            try:
                OrderLine.objects.bulk_create(create_order_lines, ignore_conflicts=False)
            except Exception as e:
                pass


@transaction.atomic
def order_delete_handler(sender, instance, using, **kwargs):
    basket = instance.basket
    basket.is_ordered = False
    basket.save()


@transaction.atomic
def order_line_save_handler(sender, instance, created, **kwargs):
    if not created:
        stuff = instance.stuff
        stuff.quantity = instance.quantity
        stuff.save()
