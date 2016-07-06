from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from master_password.compat import check_password, make_password


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
                # Hash the password if not already hashed.
                if master is None or '$' not in master:
                    master = make_password(master)
                # Validate the password and callback function.
                if check_password(password, master):
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
