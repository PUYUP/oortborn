from django.apps import AppConfig
from django.db.models.signals import post_save


class PersonConfig(AppConfig):
  name = 'apps.person'

  def ready(self):
    from django.conf import settings
    from utils.generals import get_model
    from .signals import user_save_handler, verifycodecode_save_handler

    VerifyCode = get_model('person', 'VerifyCode')

    post_save.connect(user_save_handler, sender=settings.AUTH_USER_MODEL,
                      dispatch_uid='user_save_signal')

    post_save.connect(verifycodecode_save_handler, sender=VerifyCode,
                      dispatch_uid='verifycodecode_save_signal')
