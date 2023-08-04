from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views import View
from .models import Team, Coach


from .forms import LoginForm, CreateCoachForm, CreateTeamForm, ManageTeamForm


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
        team.race = form.cleaned_data['race']
        team.save()

        return redirect('manage_team', team_pk=team.pk)


class ManageTeamView(FormView):
    template_name = "manage_team.html"

    def get(self, request, *args, **kwargs):
        team_pk = kwargs['team_pk']
        team = Team.objects.get(pk=team_pk)
        form = ManageTeamForm(team=team)
        players = team.players.order_by('number')
        return render(request, self.template_name, {'team': team, 'form': form, 'players': players})

    def post(self, request, *args, **kwargs):
        team_pk = kwargs['team_pk']
        team = Team.objects.get(pk=team_pk)
        form = ManageTeamForm(request.POST, team=team)
        if form.is_valid():
            player = form.save(commit=False)
            player.player_team = team
            position_selected = form.cleaned_data.get('position')
            player.movement = position_selected.movement
            player.strength = position_selected.strength
            player.agility = position_selected.agility
            player.armor = position_selected.armor
            player.passing = position_selected.passing
            player.value = position_selected.cost
            player.save()
            player.traits.set(position_selected.traits.all())
            player.skills.set(position_selected.starting_skills.all())
            player.primary_skill_categories.set(position_selected.primary_skill_categories.all())
            player.secondary_skill_categories.set(position_selected.secondary_skill_categories.all())
            team.treasury -= player.position.cost
            team.save()
            return redirect('manage_team', team_pk=team.pk)
        else:
            players = team.players.all()
            return render(request, self.template_name, {'team': team, 'form': form, 'players': players})


class MainPageView(View):
    pass
