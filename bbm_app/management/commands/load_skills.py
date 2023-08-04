import json
from django.core.management.base import BaseCommand
from bbm_app.models import Skill, SkillCategory


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
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
