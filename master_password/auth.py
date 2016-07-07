import warnings

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import check_password, make_password
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from django.utils.translation import ugettext as _


class WeakPasswordValidationError(ValidationError):
    pass


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
            for master, callback in self.get_master_passwords().iteritems():
                # Validate the password and callback function.
                if master is None or '$' not in master:
                    # Hash the password if not already hashed.
                    master = make_password(master)

                if check_password(password, master):
                    if settings.DEBUG==False and not self.validate_password_strength(password):
                        # validate plain text password is a strong password
                        warnings.warn(message=_("When DEBUG is False, master password must be "
                                              "more than 50 characters, containing at least one "
                                              "uppercase, one lowercase, one digit and one "
                                              "non-alphanumeric character."))
                        continue
                    if callback is None or callback(user):
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
        raise NotImplemented

    def validate_password_strength(self, plain_password):
        """
        Check the password is a strong password for production use of master passwords
        """
        MIN_LENGTH = 50

        if len(plain_password) < MIN_LENGTH:
            return False

        if not any(char.isdigit() for char in plain_password):
            return False

        if not any(char.islower() for char in plain_password):
            return False

        if not any(char.isupper() for char in plain_password):
            return False

        if not any(not char.isalpha() for char in plain_password):
            return False

        return True


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


# Raise a warning if master password is used in production environment
for backend in settings.AUTHENTICATION_BACKENDS:
    if not settings.DEBUG and issubclass(import_string(backend), MasterPasswordMixin):
        warnings.warn("Warning, django-master-password is installed in a non-DEBUG environment. "
                      "Please ensure you are using a strong password if DEBUG is set to True.")
        break
