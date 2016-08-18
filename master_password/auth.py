import string
import warnings

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password, make_password
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _


class MasterPasswordMixin(object):
    """
    Adds fallback master password authentication to an existing backend.

    On each subclass, you must define:

        get_user_object(**kwargs)
            Return a user object to be validated. This will usually be the same
            as ``authenticate()`` on the super class, but without any password
            validation.

    You can also optionally override:

        get_master_passwords()
            Return a dictionary with clear text or hashed passwords as keys,
            and callback functions (or ``None``) as values.

            The callback function for each master password must take a user
            object as its only argument, and should return ``True`` if the user
            is allowed to authenticate with that password.

            The ``MASTER_PASSWORDS`` setting is returned by default.

        get_password(**kwargs)
            Return a password to be validated. The ``password`` keyword
            argument is returned as-is by default.
    """

    def authenticate(self, **kwargs):
        """
        Return a user object if authenticated by the superclass or a valid
        master password.
        """
        # First, try to authenticate with the superclass.
        user = super(MasterPasswordMixin, self).authenticate(**kwargs)
        if user is not None:
            return user
        # Fallback to master password authentication.
        user = self.get_user_object(**kwargs)
        password = self.get_password(**kwargs)
        if user and password:
            # Try all the master passwords.
            for master, callback in self.get_master_passwords().items():
                if settings.DEBUG:
                    # Check hashed and clear text versions.
                    hashed = [master, make_password(master)]
                else:
                    # Check only hashed version.
                    hashed = [master]
                for master in hashed:
                    if check_password(password, master):
                        if callback is None or callback(user):
                            # Master password *must* be strong in production.
                            if not settings.DEBUG and \
                                    not self.is_strong_password(password):
                                warnings.warn(message=_(
                                    'When DEBUG=False, master passwords must '
                                    'be more than 50 characters, with at '
                                    'least 1 uppercase, 1 lowercase, 1 digit '
                                    'and 1 non-alphanumeric character.'))
                                continue
                            return user

    def get_master_passwords(self):
        """
        Return a dictionary of master passwords.
        """
        return getattr(settings, 'MASTER_PASSWORDS', {})

    def get_password(self, password=None, **kwargs):
        """
        Return the password to be validated from the given keyword arguments.
        """
        return password

    def get_user_object(self, **kwargs):
        """
        Return a user object for the given keyword arguments.
        """
        raise NotImplemented  # pragma: no cover

    def is_strong_password(self, password):
        """
        Return `True` if the password is strong.
        """
        chars = set(password)
        is_strong = all([
            chars.intersection(string.digits),
            chars.intersection(string.ascii_lowercase),
            chars.intersection(string.ascii_uppercase),
            len(chars) >= 50,
            not password.isalnum(),
        ])
        return is_strong


class ModelBackend(MasterPasswordMixin, ModelBackend):
    """
    Add master password authentication to ``ModelBackend``.
    """

    def get_user_object(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            return user
        except UserModel.DoesNotExist:
            return None


PRODUCTION_WARNING = (
    'django-master-password is enabled and DEBUG=False. You *must* use '
    'strong hashed master passwords.')


def production_warning():
    # Issue a warning if enabled in production.
    for backend in settings.AUTHENTICATION_BACKENDS:
        if not settings.DEBUG and issubclass(
                import_string(backend), MasterPasswordMixin):
            warnings.warn(PRODUCTION_WARNING)
            break


production_warning()
