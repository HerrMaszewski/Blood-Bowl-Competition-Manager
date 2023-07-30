from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Coach, Team, Race, Player, Position, RacePositionLimit

User = get_user_model()


class LoginForm(forms.Form):
    coach_name = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        coach_name = cleaned_data.get('coach_name')
        password = cleaned_data.get('password')
        try:
            user = User.objects.get(username=coach_name)
        except User.DoesNotExist:
            raise ValidationError('Niepoprawna nazwa użytkownika lub hasło')
        if not user.check_password(password):
            raise ValidationError('Niepoprawna nazwa użytkownika lub hasło')
        try:
            coach = Coach.objects.get(user=user)
        except Coach.DoesNotExist:
            raise ValidationError('Niepoprawna nazwa użytkownika lub hasło')

        self.user = user
        self.coach = coach


class CreateCoachForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Repeat Password')

    class Meta:
        model = Coach
        fields = ('coach_name',)

    def clean_coach_name(self):
        coach_name = self.cleaned_data['coach_name']
        if Coach.objects.filter(coach_name=coach_name).exists():
            raise forms.ValidationError('Jest już trener który się tak nazywa')
        if User.objects.filter(username=coach_name).exists():
            raise forms.ValidationError('Jest już trener który się tak nazywa')
        return coach_name

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password2'):
            self.add_error('password2', 'Hasła nie są identyczne')

    def save(self, commit=True):
        user = User.objects.create_user(username=self.cleaned_data['coach_name'],
                                        password=self.cleaned_data['password'])
        user.save()
        coach = Coach(user=user, coach_name=self.cleaned_data['coach_name'])
        if commit:
            coach.save()
        return coach


class CreateTeamForm(forms.ModelForm):
    race = forms.ModelChoiceField(queryset=Race.objects.all())

    class Meta:
        model = Team
        fields = ['team_name', 'race']


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name', 'number', 'position']

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)
        if self.team:
            self.fields['position'].queryset = Position.objects.filter(race=self.team.race)
            taken_numbers = Player.objects.filter(player_team=self.team).values_list('number', flat=True)
            self.fields['number'].choices = [(i, i) for i in range(1, 17) if i not in taken_numbers]

    def clean(self):
        cleaned_data = super().clean()
        position = cleaned_data.get("position")
        if position and position.cost > self.team.treasury:
            self.add_error('position', 'Insufficient funds.')

        # Check if position limit has been reached
        race_position_limit = RacePositionLimit.objects.filter(race=self.team.race, position=position).first()
        if race_position_limit:
            position_count = self.team.players.filter(position=position).count()
            if position_count >= race_position_limit.max_count:
                self.add_error('position', 'Maximum number of this position has been reached for the team.')

    def clean_number(self):
        number = self.cleaned_data.get('number')
        if number and (number < 1 or number > 16):
            raise forms.ValidationError("Invalid number. Please choose a number between 1 and 16.")
        if number and Player.objects.filter(player_team=self.team, number=number).exists():
            raise forms.ValidationError("This number is already in use.")
        return number
