try:
    from django.contrib.auth.hashers import check_password, make_password
except ImportError:
    from django.contrib.auth.models import check_password, make_password
