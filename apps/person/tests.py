from django.test import TestCase

from utils.generals import get_model

User = get_model('person', 'User')
Account = get_model('person', 'Account')
Profile = get_model('person', 'Profile')
VerifyCode = get_model('person', 'VerifyCode')


# Create your tests here.
class AccountTestCase(TestCase):
    def setUp(self):
        self.email = 'test@email.com'
        self.msisdn = '0811806807'

        self.user = User.objects.create_user('testuser', 'my@wmail.com', '123456')
        self.passcode_email = VerifyCode.objects.create(email=self.email, is_used=False, is_expired=False)
        self.passcode_msisdn = VerifyCode.objects.create(msisdn=self.msisdn, is_used=False, is_expired=False)

    def test_account_created(self):
        account = Account.objects.get(user__id=self.user.id)
        profile = Profile.objects.get(user__id=self.user.id)
        passcode_email = VerifyCode.objects.get(email=self.email)
        passcode_msisdn = VerifyCode.objects.get(msisdn=self.msisdn)

        self.assertEqual(self.user.account, account)
        self.assertEqual(self.user.profile, profile)

        self.assertEqual(self.passcode_email, passcode_email)
        self.assertEqual(self.passcode_msisdn, passcode_msisdn)

    def test_validate_passcode(self):
        passcode_valid_email = VerifyCode.objects.validate(email=self.email, passcode=self.passcode_email.passcode)
        passcode_valid_msisdn = VerifyCode.objects.validate(msisdn=self.msisdn, passcode=self.passcode_msisdn.passcode)

        self.assertEqual(passcode_valid_email, True)
        self.assertEqual(passcode_valid_msisdn, True)
