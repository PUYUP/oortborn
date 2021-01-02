from django.conf import settings
from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import EmailValidator

from rest_framework import serializers

# PROJECT UTILS
from utils.generals import get_model, create_unique_id
from utils.validators import non_python_keyword, identifier_validator

from apps.person.api.validator import (
    EmailDuplicateValidator,
    MSISDNDuplicateValidator,
    MSISDNNumberValidator,
    PasswordValidator
)

from ..account.serializers import AccountSerializer
from ..profile.serializers import ProfileSerializer

User = get_model('person', 'User')
Account = get_model('person', 'Account')
VerifyCode = get_model('person', 'VerifyCode')


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        context = kwargs.get('context', dict())
        request = context.get('request', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        # Use this field on specific request
        if request.method == 'PATCH':
            # Only this field can us at user update
            fields = ('username', 'password', 'first_name', 'email',)

        if fields is not None and fields != '__all__':
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

class UserListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        if isinstance(value, QuerySet):
            value = value.prefetch_related(Prefetch('topic'))
        return super().to_representation(value)


class UserSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='person_api:user-detail',
                                               lookup_field='uuid', read_only=True)

    # for registration only
    # msisdn not part of User model
    # msisdn part of Account
    msisdn = serializers.CharField(required=False, write_only=True,
                                   validators=[MSISDNNumberValidator()],
                                   min_length=8, max_length=14)

    # use if action need verify code
    # eg: register, change email, ect
    token = serializers.CharField(required=False, write_only=True)
    challenge = serializers.CharField(required=False, write_only=True,
                                      validators=[non_python_keyword,
                                                  identifier_validator])

    # change password purposed
    password1 = serializers.CharField(required=False, write_only=True)
    password2 = serializers.CharField(required=False, write_only=True)

    profile = ProfileSerializer(many=False, read_only=True)
    account = AccountSerializer(many=False, read_only=True)

    class Meta:
        model = User
        list_serializer_class = UserListSerializer
        exclude = ('id', 'user_permissions', 'groups', 'date_joined',
                   'is_superuser', 'last_login', 'is_staff',)
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 6
            },
            'username': {
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'required': False,
                'validators': [EmailValidator()]
            }
        }

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        # default verifycode
        self.verifycode_obj = None

    def to_internal_value(self, data):
        # All of this only for register process
        if not self.instance:
            self.msisdn = data.pop('msisdn', None)
            self.challenge = data.pop('challenge', None)
            self.token = data.pop('token', None)
            self.email = data.get('email', None)
            self.first_name = data.get('first_name', None)
            self.username = data.get('username', None)

            # used for password change only
            self.password = data.get('password', None) # as old password
            self.password1 = data.pop('password1', None)
            self.password2 = data.pop('password2', None)

            if 'password' in self.fields:
                self.fields['password'].validators.extend([PasswordValidator()])

            if settings.STRICT_MSISDN and 'msisdn' in self.fields:
                # MSISDN required if EMAIL not provided
                if not self.email:
                    self.fields['msisdn'].required = True

                if settings.STRICT_MSISDN_DUPLICATE:
                    self.fields['msisdn'].validators.extend([MSISDNDuplicateValidator()])

            if settings.STRICT_EMAIL and 'email' in self.fields:
                # EMAIL required if MSISDN not provided
                if not self.msisdn:
                    self.fields['email'].required = True

                if settings.STRICT_EMAIL_DUPLICATE:
                    self.fields['email'].validators.extend([EmailDuplicateValidator()])

            # use username as first_name if first_name not exist
            if self.first_name is None:
                data['first_name'] = self.username

            # generate username if None
            if self.username is None:
                data['username'] = '{}{}'.format(create_unique_id(2), slugify(self.msisdn))

            # generate email if None
            if self.email is None:
                data['email'] = '{}{}@daftarbelanja.com'.format(create_unique_id(2), slugify(self.username))

            # insert msisdn
            if self.msisdn:
                data['msisdn'] = self.msisdn

            # set is_active to True
            # if False user can't loggedin
            data['is_active'] = True

        # Normalize
        data = super().to_internal_value(data)
        return data

    def validate_email(self, value):
        # check verified email
        if settings.STRICT_EMAIL_VERIFIED:
            with transaction.atomic():
                try:
                    self.verifycode_obj = VerifyCode.objects.select_for_update() \
                        .get_verified_unused(email=value, challenge=self.challenge, token=self.token)
                except ObjectDoesNotExist:
                    if self.instance:
                        # update user
                        raise serializers.ValidationError(_(u"Kode verifikasi pembaruan email salah"))
                    else:
                        # create user
                        raise serializers.ValidationError(_(u"Alamat email belum divalidasi"))
        return value

    def validate_msisdn(self, value):
        # check msisdn verified
        if settings.STRICT_MSISDN_VERIFIED:
            with transaction.atomic():
                try:
                    self.verifycode_obj = VerifyCode.objects.select_for_update() \
                        .get_verified_unused(msisdn=value, challenge=self.challenge, token=self.token)
                except ObjectDoesNotExist:
                    raise serializers.ValidationError(_(u"MSISDN belum divalidasi"))
        return value

    """
    def validate_username(self, value):
        if self.instance:
            email = self.instance.email
            msisdn = self.instance.account.msisdn

            with transaction.atomic():
                try:
                    self.verifycode_obj = VerifyCode.objects.select_for_update() \
                        .get_verified_unused(email=email, msisdn=msisdn, challenge=self.challenge,
                                             token=self.token)
                except ObjectDoesNotExist:
                    raise serializers.ValidationError(_(u"Kode verifikasi pembaruan nama pengguna salah"))
        return value
    """

    def validate_password(self, value):
        instance = getattr(self, 'instance', dict())

        # make sure password filled
        if not self.password1 or not self.password2:
            raise serializers.ValidationError(_(u"Password tidak boleh kosong"))
        
        if self.password1 != self.password2:
            raise serializers.ValidationError(_(u"Password tidak sama"))

        try:
            validate_password(self.password2)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        # change password, instance = user object
        if instance:
            username = getattr(instance, 'username', None)

            # check current password is passed
            passed = authenticate(username=username, password=self.password)
            if passed is None:
                raise serializers.ValidationError(_(u"Password lama salah"))
            return self.password2
        return value

    @transaction.atomic
    def create(self, validated_data):
        is_msisdn_verified = False
        is_email_verified = False
        msisdn = validated_data.pop('msisdn', None)

        try:
            user = get_user_model().objects.create_user(**validated_data)
        except IntegrityError as e:
            raise ValidationError(str(e))
        except TypeError as e:
            raise ValidationError(str(e))
        
        if settings.STRICT_MSISDN_VERIFIED:
            is_msisdn_verified = True

        if settings.STRICT_EMAIL_VERIFIED:
            is_email_verified = True

        # create Account instance
        account = getattr(user, 'account')
        if account:
            account.is_email_verified = is_email_verified
            account.msisdn = msisdn
            account.is_msisdn_verified = is_msisdn_verified
            account.save()
        else:
            try:
                Account.objects.create(user=user, msisdn=self.msisdn, is_msisdn_verified=is_msisdn_verified,
                                       is_email_verified=is_email_verified)
            except IntegrityError:
                pass

        # all done mark verifycode as used
        if self.verifycode_obj:
            self.verifycode_obj.mark_used()
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request', None)

        for key, value in validated_data.items():
            if hasattr(instance, key):
                # update password
                if key == 'password':
                    instance.set_password(value)

                    # add flash message
                    messages.success(request, _("Password berhasil dirubah."
                                                " Login dengan password baru Anda"))
                else:
                    old_value = getattr(instance, key, None)
                    if old_value != value:
                        setattr(instance, key, value)
        instance.save()

        # all done mark verifycode as used
        if self.verifycode_obj:
            self.verifycode_obj.mark_used()
        return instance
