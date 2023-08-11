from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Coach, Team, Race, Player, Position, RacePositionLimit

User = get_user_model()


class LoginForm(forms.Form):
    """
    A form for user login. Validates username and password.
    """

    coach_name = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        """
        Validate the form data.
        Checks if the username exists, and if the password matches the user's password.
        Also checks if a Coach instance is associated with the user.
        """
        cleaned_data = super().clean()
        coach_name = cleaned_data.get('coach_name')
        password = cleaned_data.get('password')

        # Validate the username
        try:
            user = User.objects.get(username=coach_name)
        except User.DoesNotExist:
            raise ValidationError('User does not exist')

        # Validate the password
        if not user.check_password(password):
            raise ValidationError('Invalid password')

        # Check if the user has a related coach instance
        try:
            coach = Coach.objects.get(user=user)
        except Coach.DoesNotExist:
            raise ValidationError('Coach does not exist')

        self.user = user
        self.coach = coach


class CreateCoachForm(forms.ModelForm):
    """Form for creating a new Coach. """

    # Password fields.
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Repeat Password')

    class Meta:
        """
        Provides additional settings like associated model and its fields.
        """
        # The model this form is associated with.
        model = Coach
        # The fields to include in the form.
        fields = ('coach_name',)

    def clean_coach_name(self):
        """
        Validates the 'coach_name' field.
        Checks if there's already a Coach or User with the same name.
        """
        coach_name = self.cleaned_data['coach_name']

        # Check if the coach_name already exists in Coach model
        if Coach.objects.filter(coach_name=coach_name).exists():
            raise forms.ValidationError('There is already a Coach with this name')

        # Check if the coach_name already exists in User model
        if User.objects.filter(username=coach_name).exists():
            raise forms.ValidationError('There is already a Coach with this name')

        return coach_name

    def clean(self):
        """
        Overrides the clean method for form data validation.
        Checks if 'password' and 'password2' fields are identical.
        """
        cleaned_data = super().clean()

        # Check if the passwords are identical
        if cleaned_data.get('password') != cleaned_data.get('password2'):
            self.add_error('password2', 'Passwords are not identical')

    def save(self, commit=True):
        """
        Overrides the save method for creating a user and a coach.
        """
        # Create a new user
        user = User.objects.create_user(username=self.cleaned_data['coach_name'], password=self.cleaned_data['password'])
        user.save()

        # Create a new coach
        coach = Coach(user=user, coach_name=self.cleaned_data['coach_name'])

        # Save the coach
        if commit:
            coach.save()
        return coach


class CreateTeamForm(forms.ModelForm):
    """
    Form for creating a new Team.

    Attributes:
    - race: dropdown field, provides choice of all available races
    - team_name: input field, for the name of the team
    """
    race = forms.ModelChoiceField(queryset=Race.objects.all())

    class Meta:
        """
        Provides additional settings like associated model and its fields.
        """
        model = Team
        fields = ['team_name', 'race']


class AddPlayerForm(forms.ModelForm):
    """
    Form for adding a new Player to a specific Team.

    The form adjusts the available positions according to the race of the team. It also adjusts the available
    player numbers according to the numbers already taken by existing players in the team.
    """
    class Meta:
        """
        Provides additional settings like associated model and its fields.
        """
        model = Player
        fields = ['name', 'number', 'position']

    def __init__(self, *args, **kwargs):
        """
        Initialize the form instance.

        Adjusts the queryset of 'position' to only include positions available for the race of 'team'.
        Adjusts the choices of 'number' to exclude numbers already taken by players in 'team'.
        """
        self.team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)
        if self.team:
            self.fields['position'].queryset = Position.objects.filter(race=self.team.race)
            taken_numbers = Player.objects.filter(player_team=self.team).values_list('number', flat=True)
            number_choices = [(i, i) for i in range(1, 17) if i not in taken_numbers]
            self.fields['number'] = forms.ChoiceField(
                choices=number_choices,
                label='Number',
            )

    def clean(self):
        """
        Validates the form data. Checks if the team has enough funds to add a player at the chosen
        position and whether the maximum count for that position has been reached.
        """
        cleaned_data = super().clean()
        position = cleaned_data.get("position")
        if position and position.cost > self.team.treasury:
            self.add_error('position', 'Insufficient funds.')
        race_position_limit = RacePositionLimit.objects.filter(race=self.team.race, position=position).first()
        if race_position_limit:
            position_count = self.team.players.filter(position=position).count()
            if position_count >= race_position_limit.max_count:
                self.add_error('position', 'Maximum number of this position has been reached for the team.')


class SelectTeamForm(forms.Form):
    """
    A form for selecting a Team from the teams associated with the current user.
    """
    # A dropdown field for Team, queryset will be assigned in the __init__ method.
    team = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        """
        Initialize the form. Updates the 'team' field queryset based on the user passed in kwargs.
        """
        # Pop the 'user' from kwargs.
        user = kwargs.pop('user', None)
        # Call the parent's __init__ method.
        super().__init__(*args, **kwargs)
        # Set the 'team' field's queryset to be all teams associated with the user.
        self.fields['team'].queryset = Team.objects.filter(coach=user)
