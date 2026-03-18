from django.core.management.base import BaseCommand
from django.http import HttpResponse
import sys

class Command(BaseCommand):
    help = 'Healthcheck command'

    def handle(self, *args, **options):
        self.stdout.write('OK')
        sys.exit(0)