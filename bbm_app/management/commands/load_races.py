import json
from django.core.management.base import BaseCommand
from bbm_app.models import Race


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        with open(options['json_file'], 'r') as json_file:
            data = json.load(json_file)
            for race_data in data:
                Race.objects.create(
                    race_type=race_data['race'],
                    reroll_cost=race_data['reroll_cost'],
                    has_apothecary=race_data['has_apothecary']
                )
        self.stdout.write(self.style.SUCCESS('Rasy dodane'))
