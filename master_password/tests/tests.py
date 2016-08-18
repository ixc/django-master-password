"""
Tests for ``master_password`` app.
"""

# WebTest API docs: http://webtest.readthedocs.org/en/latest/api.html

import string
import warnings

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.test import override_settings
from django.test.utils import captured_stdin, captured_stdout
from django_dynamic_fixture import G
from django_webtest import WebTest

from master_password.auth import PRODUCTION_WARNING, production_warning

User = get_user_model()

CHARS = string.digits + string.ascii_lowercase + string.ascii_uppercase + \
    string.punctuation

MASTER_PASSWORDS = {
    'user123': lambda u: not u.is_staff and not u.is_superuser,
    make_password('staff123'): lambda u: u.is_staff,
    'superuser123': None,
    'strong' + CHARS: None,
    make_password('hashed' + CHARS): None
}


class Auth(WebTest):
    """
    Tests for the ``auth`` module.
    """

    @override_settings(DEBUG=True, MASTER_PASSWORDS=MASTER_PASSWORDS)
    def test_ModelBackend(self):
        # Create a user account.
        user = G(User)
        user.set_password(CHARS)
        user.save()

        # Create a staff account.
        staff = G(User, is_staff=True)
        staff.set_password(CHARS)
        staff.save()

        # Create a superuser account.
        superuser = G(User, is_superuser=True)
        superuser.set_password(CHARS)
        superuser.save()

        # Normal password validation still works.
        self.assertFalse(self.client.login(username='wrong', password='wrong'))
        self.assertFalse(self.client.login(username='wrong', password=CHARS))
        self.assertFalse(self.client.login(
            username=user.username, password='wrong'))
        self.assertTrue(self.client.login(
            username=user.username, password=CHARS))

        # Master passwords can apply to all users, if no callback is defined.
        self.assertTrue(self.client.login(
            username=user.username, password='superuser123'))
        self.assertTrue(self.client.login(
            username=superuser.username, password='superuser123'))

        # Or just a subset of users.
        self.assertTrue(self.client.login(
            username=user.username, password='user123'))
        self.assertFalse(self.client.login(
            username=superuser.username, password='user123'))

        # You can store hashed master passwords instead of clear text.
        self.assertTrue(self.client.login(
            username=staff.username, password='staff123'))

        # When DEBUG is False, you *must* use strong, hashed master passwords.
        with override_settings(DEBUG=False):
            # Weak, plain text.
            self.assertFalse(self.client.login(
                username=user.username, password='superuser123'))
            # Weak, hashed.
            self.assertFalse(self.client.login(
                username=staff.username, password='staff123'))
            # Strong, plain text.
            self.assertFalse(self.client.login(
                username=user.username, password='strong' + CHARS))
            # Strong, hashed.
            self.assertTrue(self.client.login(
                username=user.username, password='hashed' + CHARS))

    # @override_settings(DEBUG=False)
    # def test_production_warning(self):
    #     # See: https://docs.python.org/3/library/warnings.html#testing-warnings
    #     with warnings.catch_warnings(record=True) as w:
    #         warnings.simplefilter('always')
    #         production_warning()
    #         self.assertEqual(len(w), 1)
    #         self.assertEqual('%s' % w[-1].message, PRODUCTION_WARNING)


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
                'Hashed password: pbkdf2_sha256$', stdout.getvalue())
