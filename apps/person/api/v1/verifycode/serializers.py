from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from utils.mixin.validators import CleanValidateMixin

User = get_user_model()
VerifyCode = get_model('person', 'VerifyCode')


class VerifyCodeFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        data = kwargs.get('data', None)
        context = kwargs.get('context', None)
        request = context.get('request', None)

        if data:
            email = data.get('email', None)
            msisdn = data.get('msisdn', None)
            account = data.get('account', None)

            if request.method == 'POST' and (not email or not msisdn or not account):
                if account:
                    self.fields.pop('msisdn')
                    self.fields.pop('email')
                else:
                    if email:
                        self.fields.pop('msisdn')
                    elif msisdn:
                        self.fields.pop('email')

                    try:
                        self.fields.pop('account')
                    except KeyError:
                        pass


class VerifyCodeSerializer(VerifyCodeFieldsModelSerializer, CleanValidateMixin,
                           serializers.ModelSerializer):
    credential = serializers.CharField(read_only=True)

    class Meta:
        model = VerifyCode
        fields = ('uuid', 'credential', 'email', 'msisdn', 'challenge', 'token', 'valid_until',)
        read_only_fields = ('uuid', 'token',)
        extra_kwargs = {
            'challenge': {
                'required': True
            },
            'msisdn': {
                'required': True,
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'required': True
            },
        }

    def get_msisdn(self, obj):
        if obj.msisdn:
            return obj.msisdn
        else:
            request = self.context.get('request', None)
            user = request.user
            return user.account.msisdn

    def to_internal_value(self, data):
        email = data.get('email', None)
        msisdn = data.get('msisdn', None)
        credential = data.get('credential', None)

        # normalize
        data = super().to_internal_value(data)

        # fill email by user found
        # TODO: use msisdn
        if credential and not email and not msisdn:
            try:
                user = User.objects.get(Q(username=credential) | Q(email=credential) | Q(account__msisdn=credential))
                data['email'] = getattr(user, 'email', None)
            except ObjectDoesNotExist:
                pass
        return data

    def to_representation(self, value):
        action = self.context.get('action', None)
        info = _("Terjadi kesalahan")

        if action == 'validate':
            info = _("Validasi berhasil")
        else:
            if value.email:
                info = _("Kode verifikasi dikirim ke email <strong>{email}</strong>".format(email=value.email))

            if value.msisdn:
                info = _("Kode verifikasi dikirim ke nomor <strong>{msisdn}</strong>".format(msisdn=value.msisdn))

        # capture data from context params
        request = self.context.get('request', None)
        user = request.user

        # normalize
        ret = super().to_representation(value)

        if hasattr(value, 'msisdn'):
            ret['msisdn'] = value.msisdn
        else:
            if user:
                account = getattr(user, 'account', dict())
                ret['msisdn'] = getattr(account, 'msisdn', None)

        if hasattr(value, 'email'):
            ret['email'] = value.email
        else:
            if user:
                ret['email'] = user.email

        # this data not for validate response
        if action == 'create':
            ret['is_create'] = True

        # prepare for password recovery
        password_recovery_token = self.context.get('password_recovery_token', None)
        password_recovery_uidb64 = self.context.get('password_recovery_uidb64', None)
        if password_recovery_token and password_recovery_uidb64:
            ret['password_recovery_token'] = password_recovery_token
            ret['password_recovery_uidb64'] = password_recovery_uidb64
        
        ret['info'] = info
        return ret

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request', None)
        email = validated_data.pop('email', None)
        msisdn = validated_data.pop('msisdn', None)
        challenge = validated_data.pop('challenge', None)
        user_agent = request.META['HTTP_USER_AGENT']

        if not email and not msisdn:
            raise NotAcceptable(_(u"Email, msisdn or account required (one of these)"))

        _defaults = {
            'challenge': challenge,
            'user_agent': user_agent,
            'is_verified': False,
            'is_used': False,
            'is_expired': False,
        }

        if email and not msisdn:
            _defaults['email'] = email

        if msisdn and not email:
            _defaults['msisdn'] = msisdn

        # Ops, please choose one (email or telehone)
        if msisdn and email:
            raise NotAcceptable(_(u"Only accept one of email or msisdn"))

        # If `valid_until` greater than time now we update VerifyCode Code
        obj, _created = VerifyCode.objects \
            .filter(Q(valid_until__gt=timezone.now())) \
            .update_or_create(**_defaults, defaults=_defaults) 

        return obj

    @transaction.atomic
    def update(self, instance):
        action = self.context.get('action', None)

        # update verifycode
        if action == 'validate':
            # this mean validate verifycode send in email or msisdn
            instance.save(update_fields=['is_verified'])
        else:
            # this mean request new verifycode
            instance.save(update_fields=['passcode', 'token', 'valid_until',
                                        'valid_until_timestamp'])

        return instance
