from django.db import transaction, IntegrityError
from django.db.models import Q, Case, When, Value
from django.contrib.auth.models import Group

from utils.generals import get_model
from .utils.constants import DEFAULT_GROUP

# Celery task
from apps.person.tasks import send_verifycode_email

Account = get_model('person', 'Account')
Profile = get_model('person', 'Profile')


@transaction.atomic
def user_save_handler(sender, instance, created, **kwargs):
    if created:
        account = getattr(instance, 'account', None)
        if account is None:
            try:
                Account.objects.create(user=instance, email=instance.email)
            except IntegrityError:
                pass

        profile = getattr(instance, 'profile', None)
        if profile is None:
            try:
                Profile.objects.create(user=instance)
            except IntegrityError:
                pass

        # Get groups if user created by admin
        groups_input = getattr(instance, 'groups_input', None)
        if groups_input is None:
            # This action indicate user self registration
            # Set default user groups
            instance.groups.add(Group.objects.get(name=DEFAULT_GROUP))

    if not created:
        # create Account if not exist
        if not hasattr(instance, 'account'):
            Account.objects.create(user=instance, email=instance.email)
        else:
            instance.account.email = instance.email
            instance.account.save()

        # create Profile if not exist
        if not hasattr(instance, 'profile'):
            Profile.objects.create(user=instance)


@transaction.atomic
def verifycodecode_save_handler(sender, instance, created, **kwargs):
    # create tasks
    # run only on resend and created
    if instance.is_used == False and instance.is_verified == False:
        if instance.email:
            data = {
                'email': getattr(instance, 'email', None),
                'passcode': getattr(instance, 'passcode', None)
            }
            send_verifycode_email.delay(data) # with celery
            # send_verifycode_email(data) # without celery

        # mark older VerifyCode Code to expired
        oldest = instance.__class__.objects \
            .filter(
                Q(challenge=instance.challenge),
                Q(is_used=False), Q(is_expired=False),
                Q(email=Case(When(email__isnull=False, then=Value(instance.email))))
                | Q(msisdn=Case(When(msisdn__isnull=False, then=Value(instance.msisdn))))
            ).exclude(passcode=instance.passcode)

        if oldest.exists():
            oldest.update(is_expired=True)
