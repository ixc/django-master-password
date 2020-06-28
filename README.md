[![Build Status](https://img.shields.io/travis/ixc/django-master-password.svg)](https://travis-ci.org/ixc/django-master-password)
[![Coverage Status](https://img.shields.io/coveralls/ixc/django-master-password.svg)](https://coveralls.io/github/ixc/django-master-password)
[![Version](https://img.shields.io/pypi/v/django-master-password.svg)](https://pypi.python.org/pypi/django-master-password)

# Overview

This app provides a mixin class that adds fallback master password
authentication to an existing backend, and a ready to use subclass of Django's
`ModelBackend` with master password authentication.

This could be dangerous and is generally not recommended for production, but is
super handy for development and staging environments.

In a pinch it can also be used temporarily (with a strong password) to
troubleshoot end-user issues in production environments, without having to
reset their password.

# Installation

Install with pip:

    $ pip install django-master-password

Update the `AUTHENTICATION_BACKENDS` setting:

    AUTHENTICATION_BACKENDS += ('master_password.auth.ModelBackend', )

If you want to use the optional `make_password` management command, update the
`INSTALLED_APPS` setting as well:

    INSTALLED_APPS += ('master_password', )

# Usage

The `MasterPasswordMixin.authenticate()` method will first try to authenticate
with its superclass, and then it will fallback to master password
authentication.

The default implementation authenticates against the `MASTER_PASSWORDS`
setting, which should be a dictionary with clear text or hashed passwords as
keys, and callback functions (or `None`) as values.

A callback function must take a user object as its only argument, and should
return `True` if the user is allowed to authenticate with that password.

For example, you might have one master password that cannot be used for staff
or superuser accounts, and another that can be used for any account:

    MASTER_PASSWORDS = {
        'user123': lambda u: not u.is_staff and not u.is_superuser,
        'superuser123': None,
    }

The use of clear text master passwords is intended as a convenience during
development. When `DEBUG=False`, you *must* use a strong hashed password with
at least 50 characters, 1 digit, 1 uppercase letter, 1 lowercase letter, and 1
non-alphanumeric character:

    MASTER_PASSWORDS = {
        'pbkdf2_sha256$'
        '20000$'
        'kGdCcfmJtsUY$'
        'euTmHbJ9sdHirlsM2MvUjHQPDJ6CZdu02gYrxY3aAbI=': None,
    }

This is a failsafe against accidentally enabling an unsafe master password for
production and staging environments.

You can generate a hashed password in Python:

    >>> from django.contrib.auth.hashers import make_password
    >>> print make_password('password123')
    pbkdf2_sha256$20000$kGdCcfmJtsUY$euTmHbJ9sdHirlsM2MvUjHQPDJ6CZdu02gYrxY3aAbI=

Or use the `make_password` management command:

    (venv)$ ./manage.py make_password
    Password:
    Hashed password: pbkdf2_sha256$20000$kGdCcfmJtsUY$euTmHbJ9sdHirlsM2MvUjHQPDJ6CZdu02gYrxY3aAbI=

# Customising

If you are already using a custom auth backend, use the mixin class to add
master password authentication to it. You will need to define a
`get_user_object(**kwargs)` method, which should be the same as the
`authenticate()` method on the superclass but without any password validation.

You can also override the `get_master_passwords()` method if you want to get
master passwords from another source than the `MASTER_PASSWORDS` setting.
