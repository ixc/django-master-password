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

MASTER_PASSWORDS = {
    'user123': lambda u: not u.is_staff and not u.is_superuser,
    make_password('staff123'): lambda u: u.is_staff,
    'superuser123': None,
}


@override_settings(MASTER_PASSWORDS=MASTER_PASSWORDS)
class Auth(WebTest):
    """
    Tests for the ``auth`` module.
    """

    def test_ModelBackend(self):
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
        self.assertTrue(self.client.login(
            username=user.username, password='superuser123'))
        self.assertTrue(self.client.login(
            username=superuser.username, password='superuser123'))

        # Or just a subset of users.
        self.assertTrue(
            self.client.login(username=user.username, password='user123'))
        self.assertFalse(self.client.login(
            username=superuser.username, password='user123'))

        # You can store hashed master passwords instead of clear text.
        self.assertTrue(self.client.login(
            username=staff.username, password='staff123'))


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
