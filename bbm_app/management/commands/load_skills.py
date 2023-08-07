import json
from django.core.management.base import BaseCommand
from bbm_app.models import Skill, SkillCategory


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
        then uses this data to get or create instances of Skills in the application's database.
        """
        with open(options['json_file'], 'r') as json_file:
            data = json.load(json_file)
            for category_skills in data:
                category_name = category_skills['category']
                print(f'Processing category: {category_name}')
                category, created = SkillCategory.objects.get_or_create(name=category_name)
                for skill_name in category_skills['skills']:
                    print(f'Processing skill: {skill_name}')
                    skill, created = Skill.objects.get_or_create(name=skill_name)
                    category.skills.add(skill)
        self.stdout.write(self.style.SUCCESS('Skills added'))
