import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _


# Extend User
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#substituting-a-custom-user-model
class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta(AbstractUser.Meta):
        app_label = 'person'

    @property
    def is_customer(self):
        return False

    @property
    def is_assistant(self):
        return False
