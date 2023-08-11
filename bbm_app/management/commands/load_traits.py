import json
from django.core.management.base import BaseCommand
from bbm_app.models import Trait


class Command(BaseCommand):
    """
    This class represents a custom management command for a Django application.
    The command reads data from JSON files in a specified directory and populates the application's database with that data.
    """

    def add_arguments(self, parser):
        """
        This method defines the arguments that can be passed to the command from the command line.
        In this case, one argument 'json_dir' is added, which should point to the directory containing the JSON files.
        """
        parser.add_argument('json_dir', type=str)

    def handle(self, *args, **options):
        """
        This method is the main logic of the command.

        It reads data from JSON files in the directory specified by the 'json_dir' argument,
        then uses this data to get or create instances of Traits in the application's database.
        """
        with open(options['json_file'], 'r') as json_file:
            data = json.load(json_file)
            for trait in data:
                Trait.objects.create(name=trait['name'])
        self.stdout.write(self.style.SUCCESS('Traits added'))
