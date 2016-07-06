import os

# DJANGO ######################################################################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

DEBUG = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'master_password.urls'
SECRET_KEY = 'secret-key'
STATIC_URL = '/static/'

# MASTER PASSWORD #############################################################

AUTHENTICATION_BACKENDS = ('master_password.auth.ModelBackend', )

INSTALLED_APPS += (
    'master_password',
    'master_password.tests',
)

# NOSE ########################################################################

INSTALLED_APPS += ('django_nose', )
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'  # Default: django.test.runner.DiscoverRunner

NOSE_ARGS = [
    '--with-progressive',  # See https://github.com/erikrose/nose-progressive
]

# TRAVIS ######################################################################

if 'TRAVIS' in os.environ:

    # Disable progressive plugin, which doesn't work properly on Travis.
    NOSE_ARGS.remove('--with-progressive')
