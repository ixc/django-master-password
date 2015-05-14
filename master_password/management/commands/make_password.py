import getpass
import sys

from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import make_password
from six.moves import input


class Command(NoArgsCommand):
    help = 'Creates a hashed version of a password.'

    def handle_noargs(self, **options):
        # We can't redirect stdin to `getpass()` so we have to fallback to
        # `input()` to test. See: http://pymotw.com/2/getpass/
        prompt = getpass.getpass if sys.stdin.isatty() else input
        try:
            password = make_password(prompt())
        # TODO: Not sure if there is any way to test this?
        except KeyboardInterrupt:
            self.stderr.write("\nOperation cancelled.")
            sys.exit(1)
        self.stdout.write('Hashed password: %s' % password)
