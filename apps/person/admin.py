from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Prefetch

from utils.generals import get_model
from apps.person.forms import UserChangeFormExtend, UserCreationFormExtend

User = get_model('person', 'User')
Profile = get_model('person', 'Profile')
Account = get_model('person', 'Account')
VerifyCode = get_model('person', 'VerifyCode')
Permission = get_model('auth', 'Permission')


class ProfileInline(admin.StackedInline):
    model = Profile


class AccountInline(admin.StackedInline):
    model = Account
    readonly_fields = ('email',)


class UserExtend(UserAdmin):
    form = UserChangeFormExtend
    add_form = UserCreationFormExtend
    inlines = [ProfileInline, AccountInline,]
    list_display = ('username', 'first_name', 'email', 'msisdn', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email',)}),
        (_(u"Personal info"), {'fields': ('first_name', 'last_name',)}),
        (_(u"Permissions"), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',),
        }),
        (_(u"Important dates"), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password1', 'password2', 'groups',)
        }),
    )

    def msisdn(self, obj):
        return obj.account.msisdn
    msisdn.short_description = _(u"MSISDN")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        queryset = qs \
            .prefetch_related(Prefetch('account'), Prefetch('profile')) \
            .select_related('account', 'profile')
        return queryset


class VerifyCodeExtend(admin.ModelAdmin):
    model = VerifyCode
    list_display = ('email', 'msisdn', 'passcode', 'challenge', 'is_verified',
                    'is_used', 'is_expired', 'token',)
    list_display_links = ('email', 'msisdn',)
    readonly_fields = ('passcode', 'token', 'valid_until', 'valid_until_timestamp',)

    def get_readonly_fields(self, request, obj=None):
        # Disallow edit
        if obj:
            return list(set(
                [field.name for field in self.opts.local_fields] +
                [field.name for field in self.opts.local_many_to_many]))
        return super().get_readonly_fields(request, obj)

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)


admin.site.register(User, UserExtend)
admin.site.register(VerifyCode, VerifyCodeExtend)
