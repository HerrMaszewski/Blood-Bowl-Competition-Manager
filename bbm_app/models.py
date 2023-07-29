from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError


class Coach(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coach_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.coach_name


class SkillCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    skills = models.ManyToManyField('Skill', related_name='categories')

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Race(models.Model):
    RACE_CHOICES = [
        ('AMA', 'Amazon'),
        ('CDW', 'Chaos Dwarf'),
        ('CHA', 'Chaos Chosen'),
        ('DWF', 'Dwarf'),
        ('ELV', 'Elven Union'),
        ('GOB', 'Goblin'),
        ('HAF', 'Halfling'),
        ('HUM', 'Human'),
        ('LIZ', 'Lizardmen'),
        ('NEC', 'Necromantic Horror'),
        ('NOR', 'Norse'),
        ('OGR', 'Ogre'),
        ('ORC', 'Orc'),
        ('SKA', 'Skaven'),
        ('UND', 'Undead'),
        ('WOD', 'Wood Elf'),
        ('BLA', 'Black Orc'),
        ('IMP', 'Imperial Nobility'),
        ('SNO', 'Snotling'),
        ('OWA', 'Old World Alliance'),
        ('DAR', 'Dark Elf'),
        ('HIG', 'High Elf'),
        ('NUR', 'Nurgle'),
        ('KHO', 'Khorne')
    ]
    race_type = models.CharField(max_length=3, choices=RACE_CHOICES, unique=True, blank=True)
    reroll_cost = models.IntegerField(default=0)
    has_apothecary = models.BooleanField(default=True)
    positions = models.ManyToManyField('Position', through='RacePositionLimit')

    def __str__(self):
        return self.get_race_type_display()


class Trait(models.Model):
    name = models.CharField(max_length=16)

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=200)
    movement = models.IntegerField(default=0)
    strength = models.IntegerField(default=0)
    agility = models.IntegerField(default=0)
    armor = models.IntegerField(default=0)
    passing = models.IntegerField(default=0, null=True, blank=True)
    traits = models.ManyToManyField(Trait, blank=True)
    starting_skills = models.ManyToManyField(Skill, blank=True)
    cost = models.IntegerField()
    primary_skill_categories = models.ManyToManyField(SkillCategory, related_name='primary_positions')
    secondary_skill_categories = models.ManyToManyField(SkillCategory, related_name='secondary_positions', blank=True)

    def __str__(self):
        return self.name


class RacePositionLimit(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    max_count = models.IntegerField()

    class Meta:
        unique_together = ('race', 'position')

    def __str__(self):
        return f'{self.race.get_race_type_display()} {self.position} (Max: {self.max_count})'


class Graveyard(models.Model):
    players = models.ManyToManyField('Player', related_name='dead')


class Team(models.Model):
    coach = models.OneToOneField(Coach, on_delete=models.CASCADE, related_name='team')
    team_name = models.CharField(max_length=100, unique=True,)
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    team_funds = models.IntegerField(default=1000000)
    team_re_roll = models.IntegerField(default=0)
    fan_factor = models.IntegerField(default=0)
    assistant_coaches = models.IntegerField(default=0)
    cheerleaders = models.IntegerField(default=0)
    apothecary = models.BooleanField(default=False)
    players = models.ManyToManyField('Player', related_name='teams')

    def __str__(self):
        return self.team_name

    def check_position_limits(self):
        race_positions = self.race.positions.all()

        for position in race_positions:
            position_limit = RacePositionLimit.objects.get(race=self.race, position=position).max_count
            player_count = self.players.filter(position=position).count()

            if player_count > position_limit:
                raise ValidationError(f'Team {self.team_name} has too many players of position {position.name}. Maximum is {position_limit}')

    def fill_journeyman(self):
        active_players = self.players.filter(is_active=True)

        if active_players.count() < 11:
            cheapest_position = self.race.positions.order_by('cost').first()

            for i in range(11 - active_players.count()):
                taken_numbers = self.players.values_list('number', flat=True)
                available_numbers = set(range(1, 17)) - set(taken_numbers)
                player_number = min(available_numbers)

                journeyman = Player.objects.create(
                    name=f'Journeyman {i+1}',
                    position=cheapest_position,
                    is_journeyman=True,
                    number=player_number,
                    status='active',
                )
                self.players.add(journeyman)

    def save(self, *args, **kwargs):
        self.check_position_limits()
        super().save(*args, **kwargs)


class Player(models.Model):
    LEVEL_CHOICES = [
        (1, 'Rookie'),
        (2, 'Experienced'),
        (3, 'Veteran'),
        (4, 'Star'),
        (5, 'Super Star'),
        (6, 'Legend'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('injured', 'Injured'),
        ('dead', 'Dead'),
    ]

    name = models.CharField(max_length=64)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name='active_players')
    former_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name='former_players')
    graveyard = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='dead_players')
    level = models.PositiveIntegerField(choices=LEVEL_CHOICES)
    spp = models.PositiveIntegerField()
    value = models.PositiveIntegerField()
    movement = models.IntegerField(default=0)
    strength = models.IntegerField(default=0)
    agility = models.IntegerField(default=0)
    armor = models.IntegerField(default=0)
    passing = models.IntegerField(default=0)
    skills = models.ManyToManyField(Skill, related_name='current_skills')
    traits = models.ManyToManyField(Trait)
    is_journeyman = models.BooleanField(default=False)
    number = models.PositiveIntegerField(null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')


    class Meta:
        unique_together = ('team', 'number')

    def calculate_value(self):
        # Calculate the player's value
        pass

    def check_level_up(self):
        # Check if the player can level up
        pass

    def die(self):
        # Remove the player from the team
        self.team = None
        # Reset the player's number
        self.number = None
        # Set the player's value to 0
        self.value = 0
        # Save changes
        self.save()
        # Add the player to the team's graveyard
        self.teams.first().graveyard.players.add(self)

    def save(self, *args, **kwargs):
        if self.number < 1 or self.number > 16:
            raise ValidationError('Player number must be between 1 and 16.')
        if self.team and self.team.players.filter(number=self.number).exists():
            raise ValidationError(f'Player number {self.number} already exists on this team.')
        super().save(*args, **kwargs)
