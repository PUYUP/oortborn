from django.db import transaction
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, NotAcceptable

from firebase_admin.auth import get_user_by_phone_number

from utils.generals import get_model
from apps.person.utils.constants import PASSWORD_RECOVERY
from apps.person.utils.auth import get_users_by_email
from .serializers import VerifyCodeSerializer

VerifyCode = get_model('person', 'VerifyCode')


class VerifyCodeApiView(viewsets.ViewSet):
    """
    POST
    ---------------

    Param:

        {
            "account": "admin",
            "email": "my@email.com",
            "msisdn": "09284255",
            "challenge": "email_validation"
        }
    
    Rules:

        account use for registered user
        If email provided, msisdn not required
        If msisdn provide, email not required
    """
    lookup_field = 'passcode'
    lookup_value_regex = '[^/]+'
    permission_classes = (AllowAny,)

    @property
    def queryset(self):
        q = VerifyCode.objects
        return q

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request, 'action': 'create'}
        serializer = VerifyCodeSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None):
        context = {'request': self.request, 'action': 'update'}
    
        try:
            email = request.data.get('email', None)
            msisdn = request.data.get('msisdn', None)

            instance = self.queryset.select_for_update() \
                .get_unverified_unused(email=email, msisdn=msisdn, uuid=uuid)
        except ValidationError as err:
            raise NotAcceptable(detail=_(' '.join(err.messages)))
        except ObjectDoesNotExist:
            raise NotFound(_("Kode VerifyCode tidak ditemukan"))

        serializer = VerifyCodeSerializer(instance, data=request.data, partial=True,
                                          context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Sub-action validate verifycode
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['patch'], detail=True, permission_classes=[AllowAny],
            url_path='validate', url_name='validate', lookup_field='passcode')
    def validate(self, request, passcode=None):
        """
        POST
        --------------

        Format:

            {
                "email": "string",
                "msisdn": "string",
                "token": "string",
                "passcode": "string",
                "challenge": "string"
            }
        """
        context = {'request': request}

        email = request.data.get('email', None)
        msisdn = request.data.get('msisdn', None)
        challenge = request.data.get('challenge', None)
        token = request.data.get('token', None)
        provider = request.data.get('provider', None)
        provider_value = request.data.get('provider_value', None)

        if (not email and not msisdn) or not challenge or not token or not passcode:
            raise NotAcceptable(_(u"Required parameter not provided."
                                  " Required email or msisdn, challenge and token"))

        # jika menggunakan firebase maka verify code tidak terkirim
        # solusinya, kita memvalidasi otp dari firebase disini
        # jika valid maka tandai verify code valid
        # jika dari firebase 'passcode' pada object tidak dibutuhkan
        try:
            if not passcode.isupper():
                passcode = passcode.upper()

            # provider from firebase we dont need passcode
            # but we check msisdn has validated in firebase
            if provider == 'firebase':
                if msisdn:
                    passcode = None
                    msisdn_intl = msisdn.replace('0', '+62', 1);

                    try:
                       firebase_user = get_user_by_phone_number(msisdn_intl)
                       firebase_msisdn = firebase_user._data.get('phoneNumber')
                       if firebase_msisdn != provider_value:
                           raise NotAcceptable(detail=_(u"MSISDN tidak terdaftar"))
                    except:
                        raise NotAcceptable(detail=_(u"Kode verifikasi salah"))

            verifycode_obj = self.queryset.select_for_update() \
                .get_unverified_unused(email=email, msisdn=msisdn, token=token,
                                       challenge=challenge, passcode=passcode)
        except ObjectDoesNotExist:
            raise NotAcceptable(detail=_(u"Kode verifikasi salah atau kadaluarsa"))

        try:
            verifycode_obj.validate()
        except ValidationError as e:
            return Response(
                {'detail': _(u" ".join(e.messages))},
                status=response_status.HTTP_403_FORBIDDEN)

        # if password recovery request and user not logged-in
        if not request.user.is_authenticated and challenge == PASSWORD_RECOVERY:
            token = None
            uidb64 = None

            if email:
                users = get_users_by_email(email)
                for user in users:
                    token = default_token_generator.make_token(user)
                    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                    break

            if msisdn:
                # TODO: SMS verifycode
                pass

            if token and uidb64:
                context['password_recovery_token'] = token
                context['password_recovery_uidb64'] = uidb64

        context['action'] = 'validate'
        serializer = VerifyCodeSerializer(verifycode_obj, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
