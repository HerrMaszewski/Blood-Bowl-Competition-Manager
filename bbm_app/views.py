from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

from django.views.generic.edit import FormView
from django.views import View
from .models import Race, Team, Coach


from .forms import LoginForm, CreateCoachForm, CreateTeamForm


class LoginView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = reverse_lazy('main')

    def form_valid(self, form):
        login(self.request, form.user)
        return super().form_valid(form)


class RegistrationView(FormView):
    template_name = 'registration.html'
    form_class = CreateCoachForm
    success_url = reverse_lazy('create_team')

    def form_valid(self, form):
        coach = form.save()
        username = form.cleaned_data.get('coach_name')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
        return super().form_valid(form)


class CreateTeamView(FormView):
    form_class = CreateTeamForm
    template_name = 'create_team.html'

    def form_valid(self, form):
        team = form.save(commit=False)
        team.coach = Coach.objects.get(user=self.request.user)
        team.race = form.cleaned_data['race']  # This is already a Race object, so assign it directly
        team.save()

        self.request.session['team_id'] = team.id

        return redirect('manage_team', team_id=team.id)


class ManageTeamView(View):
    def get(self, request, team_id):
        team = Team.objects.get(id=team_id)
        pass


class MainPageView(View):
    pass
