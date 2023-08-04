import json
from django.core.management.base import BaseCommand
from bbm_app.models import Trait


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        with open(options['json_file'], 'r') as json_file:
            data = json.load(json_file)
            for trait in data:
                Trait.objects.create(name=trait['name'])
        self.stdout.write(self.style.SUCCESS('Traits added'))
