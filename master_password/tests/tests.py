"""
Tests for ``master_password`` app.
"""

# WebTest API docs: http://webtest.readthedocs.org/en/latest/api.html

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.test import override_settings
from django.test.utils import captured_stdin, captured_stdout
from django_dynamic_fixture import G
from django_webtest import WebTest

from master_password import auth

User = get_user_model()

WEAK_MASTER_PASSWORDS = {
    # weak simple user password, with callback to check user is not staff or super
    'user123': lambda u: not u.is_staff and not u.is_superuser,
    # weak hashed password, callback to check user is staff
    make_password('staff123'): lambda u: u.is_staff,
    # weak master password, no callback, can be used for all users
    'superuser123': None,
}

allowed_chars = 'abcdefghijklmnopqustuvwxyzABCDEFGHIJKLMNOPQUSTUVWXYZ!@#%^&*()_+-={}[];<>,./?;~`1234567890'

STRONG_USER_PASSWORD = User.objects.make_random_password(length=50, allowed_chars=allowed_chars)
HASHED_USER_PASSWORD = User.objects.make_random_password(length=50, allowed_chars=allowed_chars)
STRONG_SUPER_PASSWORD = User.objects.make_random_password(length=50, allowed_chars=allowed_chars)

STRONG_MASTER_PASSWORDS = {
    # simple user password, with callback to check user is not staff or super
    STRONG_USER_PASSWORD: lambda u: not u.is_staff and not u.is_superuser,
    # hashed password, callback to check user is staff
    make_password(HASHED_USER_PASSWORD): lambda u: u.is_staff,
    # strong master password, no callback, can be used for all users
    STRONG_SUPER_PASSWORD: None,
    'SomeWeakMasterPassword': lambda u: not u.is_staff and not u.is_superuser,
}

class Auth(WebTest):
    """
    Tests for the ``auth`` module.
    """

    @override_settings(DEBUG=True, MASTER_PASSWORDS=WEAK_MASTER_PASSWORDS)
    def test_ModelBackend(self):
        """
        DEBUG is False. We don't need a strong master_password.
        """

        # Generate a random password.
        password = User.objects.make_random_password()

        # Create a user account.
        user = G(User)
        user.set_password(password)
        user.save()

        # Create a staff account.
        staff = G(User, is_staff=True)
        staff.set_password(password)
        staff.save()

        # Create a superuser account.
        superuser = G(User, is_superuser=True)
        superuser.set_password(password)
        superuser.save()

        # Normal password validation still works.
        self.assertFalse(
            self.client.login(username='wrong', password='wrong'))
        self.assertFalse(
            self.client.login(username=user.username, password='wrong'))
        self.assertTrue(
            self.client.login(username=user.username, password=password))

        # Master passwords can apply to all users, if no callback is defined.
        self.assertTrue(
            self.client.login(username=user.username, password='superuser123'))
        self.assertTrue(
            self.client.login(username=superuser.username, password='superuser123'))

        # Or just a subset of users.
        self.assertTrue(
            self.client.login(username=user.username, password='user123'))
        self.assertFalse(
            self.client.login(username=superuser.username, password='user123'))

        # You can store hashed master passwords instead of clear text.
        self.assertTrue(
            self.client.login(username=staff.username, password='staff123'))


    @override_settings(DEBUG=False, MASTER_PASSWORDS=STRONG_MASTER_PASSWORDS)
    def test_PasswordInProduction(self):
        """
        DEBUG is True. We do need a strong master password.
        """
        # test that we are not inadvertently revealing the plain text master password

        # Generate a strong random master password.
        password = User.objects.make_random_password(length=50, allowed_chars=allowed_chars)

        # Create a user account.
        user = G(User)
        user.set_password(password)
        user.save()

        # Create a staff account.
        staff = G(User, is_staff=True)
        staff.set_password(password)
        staff.save()

        # Create a superuser account.
        superuser = G(User, is_superuser=True)
        superuser.set_password(password)
        superuser.save()

        # Normal password validation still works, but must be a strong password.
        self.assertFalse(
            self.client.login(username='wrong', password='wrong'))
        self.assertFalse(
            self.client.login(username=user.username, password='wrong'))
        self.assertTrue(
            self.client.login(username=user.username, password=password))

        # Master passwords can apply to all users, if no callback is defined.
        self.assertTrue(
            self.client.login(username=user.username, password=STRONG_SUPER_PASSWORD))
        self.assertTrue(
            self.client.login(username=staff.username, password=STRONG_SUPER_PASSWORD))
        self.assertTrue(
            self.client.login(username=superuser.username, password=STRONG_SUPER_PASSWORD))

        # Or just a subset of users.
        self.assertTrue(
            self.client.login(username=user.username, password=STRONG_USER_PASSWORD))
        self.assertFalse(
            self.client.login(username=superuser.username, password=STRONG_USER_PASSWORD))

        # You can store hashed master passwords instead of clear text.
        self.assertTrue(
            self.client.login(username=staff.username, password=password))

        # A master password must be strong if set, check that a weak password fails.
        self.assertFalse(
            self.client.login(username=user.username, password='SomeWeakMasterPassword'))


class Management(WebTest):
    """
    Tests for management commands.
    """

    def test_make_password(self):
        with captured_stdin() as stdin, captured_stdout() as stdout:
            stdin.write('password123')
            stdin.seek(0)
            call_command('make_password')
            self.assertIn(
                'Hashed password: pbkdf2_sha256$20000$', stdout.getvalue())
