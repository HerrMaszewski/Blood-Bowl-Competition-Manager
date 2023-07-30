import json
import os
from django.core.management.base import BaseCommand
from bbm_app.models import Skill, SkillCategory, Position, Race, RacePositionLimit, Trait


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('json_dir', type=str)

    def handle(self, *args, **options):
        json_dir = options['json_dir']
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]

        for json_file in json_files:
            with open(os.path.join(json_dir, json_file), 'r') as f:
                data = json.load(f)
                race_type = data['race_type']

                try:
                    race = Race.objects.get(race_type=race_type)
                except Race.DoesNotExist:
                    print(f"Race {race_type} does not exist in the database.")
                    continue

                for position_data in data['positions']:
                    position, created = Position.objects.get_or_create(name=position_data['name'], defaults={
                        'movement': position_data['movement'],
                        'strength': position_data['strength'],
                        'agility': position_data['agility'],
                        'armor': position_data['armor'],
                        'passing': position_data['passing'],
                        'cost': position_data['cost']
                    })

                    if created:
                        starting_skills = []
                        for skill_name in position_data['starting_skills']:
                            try:
                                skill = Skill.objects.get(name=skill_name)
                                starting_skills.append(skill)
                            except Skill.DoesNotExist:
                                print(f"Skill {skill_name} does not exist in the database.")
                                continue

                        position.starting_skills.set(starting_skills)

                        traits = []
                        for trait_name in position_data.get('traits', []):
                            try:
                                trait = Trait.objects.get(name=trait_name)
                                traits.append(trait)
                            except Trait.DoesNotExist:
                                print(f"Trait {trait_name} does not exist in the database.")
                                continue

                        position.traits.set(traits)

                        primary_skill_categories = [SkillCategory.objects.get(name=category_name) for category_name in
                                                    position_data['primary_skill_categories']]
                        position.primary_skill_categories.set(primary_skill_categories)

                        secondary_skill_categories = [SkillCategory.objects.get(name=category_name) for category_name in
                                                      position_data['secondary_skill_categories']]
                        position.secondary_skill_categories.set(secondary_skill_categories)

                    RacePositionLimit.objects.get_or_create(race=race, position=position,
                                                            defaults={'max_count': position_data['max_count']})

        self.stdout.write(self.style.SUCCESS('Pozycje dodane z limitami'))
