from django.contrib.auth.models import User
from django.db import models


class Coach(models.Model):
    """
    Coach model represents a coach in the Blood Bowl game.
    Each coach is tied to a unique user and has a unique name.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coach_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        """
        Returns the unique name of the coach as a string.
        """
        return self.coach_name


class SkillCategory(models.Model):
    """
    SkillCategory model represents a category of skills in the Blood Bowl game.
    Each category has a unique name and may contain multiple skills.
    """
    name = models.CharField(max_length=100, unique=True)
    skills = models.ManyToManyField('Skill', related_name='categories')

    def __str__(self):
        """
        Returns the unique name of the skill category as a string.
        """
        return self.name


class Skill(models.Model):
    """
    The Skill model represents a unique skill in the Blood Bowl game.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        """
        Returns the unique name of the skill as a string.
        """
        return self.name


class Race(models.Model):
    """
    The Race model represents the different races/teams in the Blood Bowl game.
    Each race has unique characteristics such as reroll cost, whether it has apothecary,
    and different player positions.
    """
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
        """
        Returns the display name of the race type as a string.
        """
        return self.get_race_type_display()


class Trait(models.Model):
    """
    The Trait model represents the different traits that a player in the Blood Bowl game can possess.
    """
    name = models.CharField(max_length=16)

    def __str__(self):
        """
        Returns the name of the trait as a string.
        """
        return self.name


class Position(models.Model):
    """
    The Position model represents different positions a player can play in the Blood Bowl game.
    Each position has attributes such as movement, strength, agility, armor, passing,
    traits, skills, cost, and primary/secondary skill categories.
    """
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
        """
        Returns the name of the position as a string.
        """
        return self.name


class RacePositionLimit(models.Model):
    """
    The RacePositionLimit model represents the maximum count of each position
    allowed for a given race in the Blood Bowl game.
    """
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    max_count = models.IntegerField()

    class Meta:
        unique_together = ('race', 'position')

    def __str__(self):
       """
       Returns a string representing the race, position and the maximum count for this position.
       """
       return f'{self.race.get_race_type_display()} {self.position} (Max: {self.max_count})'


# class Graveyard(models.Model):
#     players = models.ManyToManyField('Player', related_name='dead')


class Team(models.Model):
    """
    The Team model represents a team in the Blood Bowl game.
    It includes information about the team such as coach, name, race,
    treasury, number of re-rolls, fan factor, assistant coaches, cheerleaders,
    apothecary, CTV (team value), wins, losses, and draws.
    """
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name='teams')
    team_name = models.CharField(max_length=100, unique=True, null=True)
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    treasury = models.IntegerField(default=1000000)
    team_re_roll = models.IntegerField(default=0)
    fan_factor = models.IntegerField(default=1)
    assistant_coaches = models.IntegerField(default=0)
    cheerleaders = models.IntegerField(default=0)
    apothecary = models.BooleanField(default=False)
    ctv = models.PositiveIntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)

    def __str__(self):
        """
        Returns a string representation of the team, which is its name.
        """
        return self.team_name

    @property
    def CTV(self):
        """
        Computes and returns the total value of the team, based on player values,
        re-rolls, apothecary, assistant coaches, and cheerleaders.
        """
        if self.pk is None:
            return 0

        player_value = sum(player.value for player in self.players.all() if player.status == 'active')
        reroll_value = self.team_re_roll * self.race.reroll_cost
        apothecary_value = 50000 if self.apothecary else 0
        assistant_coaches_value = self.assistant_coaches * 10000
        cheerleaders_value = self.cheerleaders * 10000
        total = player_value + reroll_value + apothecary_value + assistant_coaches_value + cheerleaders_value
        return total

    @property
    def total_matches(self):
        """
        Returns the total number of matches the team has played,
        based on wins, losses, and draws.
        """
        return self.wins + self.losses + self.draws

    @property
    def reroll_cost(self):
        """
        Computes and returns the cost of a re-roll for the team.
        The cost doubles if the team has played at least one match.
        """
        if self.total_matches > 0:
            return self.race.reroll_cost * 2
        return self.race.reroll_cost

    def save(self, *args, **kwargs):
        """
        Overrides the save method to update the CTV (team value)
        before saving the team.
        """
        self.ctv = self.CTV
        super().save(*args, **kwargs)


class Player(models.Model):
    """
    The Player model represents a player in a Blood Bowl team.
    It includes information about the player such as name, position, former team,
    graveyard, level, Star Player Points (spp), value, stats (movement, strength,
    agility, armor, passing), skills, traits, skill categories, journeyman status,
    number, status, niggling injuries, and player team.
    """
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
    former_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name='former_players')
    graveyard = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='dead_players')
    level = models.PositiveIntegerField(choices=LEVEL_CHOICES, default=1)
    spp = models.PositiveIntegerField(default=0)
    value = models.PositiveIntegerField()
    movement = models.IntegerField(default=0)
    strength = models.IntegerField(default=0)
    agility = models.IntegerField(default=0)
    armor = models.IntegerField(default=0)
    passing = models.IntegerField(default=0, null=True)
    skills = models.ManyToManyField(Skill, related_name='current_skills')
    traits = models.ManyToManyField(Trait)
    primary_skill_categories = models.ManyToManyField(SkillCategory, related_name='primary_players')
    secondary_skill_categories = models.ManyToManyField(SkillCategory, related_name='secondary_players', blank=True)
    is_journeyman = models.BooleanField(default=False)
    number = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    niggling_injuries = models.IntegerField(default=0)
    player_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players', null=True)

    class Meta:
        """
        Metaclass for Player. Defines unique_together constraint for 'player_team' and 'number'.
        """
        unique_together = ('player_team', 'number')

    # def calculate_value(self):
    #     pass
    #
    # def check_level_up(self):
    #     pass

    def save(self, *args, **kwargs):
        """
        Overrides the save method for Player model.
        """
        super().save(*args, **kwargs)



# def fill_journeyman(self):
    #     active_players = self.players.filter(is_active=True)
    #
    #     if active_players.count() < 11:
    #         cheapest_position = self.race.positions.order_by('cost').first()
    #
    #         for i in range(11 - active_players.count()):
    #             taken_numbers = self.players.values_list('number', flat=True)
    #             available_numbers = set(range(1, 17)) - set(taken_numbers)
    #             player_number = min(available_numbers)
    #
    #             journeyman = Player.objects.create(
    #                 name=f'Journeyman {i+1}',
    #                 position=cheapest_position,
    #                 is_journeyman=True,
    #                 number=player_number,
    #                 status='active',
    #             )
    #             self.players.add(journeyman)