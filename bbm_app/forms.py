from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Coach, Team, Race

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
