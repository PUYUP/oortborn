from django.db import transaction

from utils.generals import get_model

Purchased = get_model('shopping', 'Purchased')
Product = get_model('shopping', 'Product')
ProductRate = get_model('shopping', 'ProductRate')


@transaction.atomic
def stuff_save_handler(sender, instance, created, **kwargs):
    _product, _created = Product.objects.get_or_create(name=instance.name, submitter=instance.user)


@transaction.atomic
def purchased_save_handler(sender, instance, created, **kwargs):
    if created:
        basket = getattr(instance, 'basket')
        basket.is_purchased = True
        basket.save()


@transaction.atomic
def purchased_stuff_save_handler(sender, instance, created, **kwargs):
    if created:
        purchased = instance.purchased
        purchased_to_user = purchased.to_user
        basket = instance.basket
        basket_user = basket.user
        stuff = instance.stuff

        # If basket creator and to_user same, mark stuff is_done!
        if basket_user.id == purchased_to_user.id:
            stuff.is_done = True
        
        # Mark stuff purchased
        stuff.is_purchased = True
        stuff.save()

        # Collect product rate
        product_rate, _created = ProductRate.objects \
            .get_or_create(name=stuff.name, location=instance.location,
                           price=instance.price, quantity=instance.quantity,
                           metric=instance.metric, submitter=basket_user)


@transaction.atomic
def share_delete_handler(sender, instance, using, **kwargs):
    stuff_objs = instance.basket.stuff.filter(user_id=instance.to_user.id)
    purchased_objs = instance.basket.purchased.filter(to_user_id=instance.to_user.id)

    if stuff_objs.exists():
        stuff_objs.delete()

    if purchased_objs.exists():
        purchased_objs.delete()


@transaction.atomic
def purchased_stuff_delete_handler(sender, instance, using, **kwargs):
    # delete Stuff if Stuff is_additional
    if instance.stuff.is_additional:
        instance.stuff.delete()
