import json
from django.core.management.base import BaseCommand
from bbm_app.models import Position, Skill, SkillCategory, Trait


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        with open(options['json_file'], 'r') as json_file:
            data = json.load(json_file)
            for position_data in data:
                position, created = Position.objects.get_or_create(name=position_data['name'],
                                                                   movement=position_data['movement'],
                                                                   strength=position_data['strength'],
                                                                   agility=position_data['agility'],
                                                                   armor=position_data['armor'],
                                                                   passing=position_data['passing'],
                                                                   cost=position_data['cost'])
                if 'traits' in position_data:
                    for trait_name in position_data['traits']:
                        trait = Trait.objects.get(name=trait_name)
                        position.traits.add(trait)
                if 'starting_skills' in position_data:
                    for skill_name in position_data['starting_skills']:
                        skill = Skill.objects.get(name=skill_name)
                        position.starting_skills.add(skill)
                if 'primary_skill_categories' in position_data:
                    for category_name in position_data['primary_skill_categories']:
                        category = SkillCategory.objects.get(name=category_name)
                        position.primary_skill_categories.add(category)
                if 'secondary_skill_categories' in position_data:
                    for category_name in position_data['secondary_skill_categories']:
                        category = SkillCategory.objects.get(name=category_name)
                        position.secondary_skill_categories.add(category)
            self.stdout.write(self.style.SUCCESS('Pozycje dla rasy dodane'))
