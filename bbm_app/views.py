from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.views import LogoutView


from .forms import LoginForm, CreateCoachForm, CreateTeamForm, AddPlayerForm, SelectTeamForm
from .models import Team, Coach


class LoginView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = reverse_lazy('main')

    def form_valid(self, form):
        login(self.request, form.user)
        return super().form_valid(form)


class LogoutView(LogoutView):
    next_page = reverse_lazy('login')


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


class CreateTeamView(LoginRequiredMixin, FormView):
    form_class = CreateTeamForm
    template_name = 'create_team.html'

    def form_valid(self, form):
        team = form.save(commit=False)
        team.coach = Coach.objects.get(user=self.request.user)
        team.race = form.cleaned_data['race']
        team.save()
        team.refresh_from_db()

        return redirect('manage_team', team_pk=team.pk)


class ManageTeamView(LoginRequiredMixin, FormView):
    template_name = "manage_team.html"

    def dispatch(self, request, *args, **kwargs):
        self.team = get_object_or_404(Team, pk=kwargs['team_pk'])
        if self.team.coach.user != request.user:
            return HttpResponseForbidden('You are not allowed to modify this team.')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        add_player_form = AddPlayerForm(team=self.team)
        players = self.team.players.order_by('number')
        return render(request, self.template_name, {'team': self.team, 'add_player_form': add_player_form, 'players': players})

    def post(self, request, *args, **kwargs):
        add_player_form = AddPlayerForm(request.POST or None, team=self.team) if 'submit_player' in request.POST else AddPlayerForm(team=self.team)
        if 'add_reroll' in request.POST:
            if self.team.treasury >= self.team.reroll_cost and self.team.team_re_roll < 8:
                self.team.treasury -= self.team.reroll_cost
                self.team.team_re_roll += 1
                self.team.save()

        elif 'add_apothecary' in request.POST:
            if self.team.treasury >= 50000 and not self.team.apothecary and self.team.race.has_apothecary:
                self.team.treasury -= 50000
                self.team.apothecary = True
                self.team.save()

        elif 'add_assistant_coach' in request.POST:
            if self.team.treasury >= 10000 and self.team.assistant_coaches < 8:
                self.team.treasury -= 10000
                self.team.assistant_coaches += 1
                self.team.save()

        elif 'add_cheerleader' in request.POST:
            if self.team.treasury >= 10000 and self.team.cheerleaders < 8:
                self.team.treasury -= 10000
                self.team.cheerleaders += 1
                self.team.save()

        if 'submit_player' in request.POST and add_player_form.is_valid():
            player = add_player_form.save(commit=False)
            player.player_team = self.team
            position_selected = add_player_form.cleaned_data.get('position')
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
            self.team.treasury -= player.position.cost
            self.team.save()

        players = self.team.players.all()
        return render(request, self.template_name, {'team': self.team, 'add_player_form': add_player_form, 'players': players})


class MainPageView(LoginRequiredMixin, View):
    template_name = 'main.html'

    def get(self, request, *args, **kwargs):
        select_team_form = SelectTeamForm(user=request.user.coach)
        return render(request, self.template_name, {'select_team_form': select_team_form})


class SelectTeamView(LoginRequiredMixin, FormView):
    form_class = SelectTeamForm
    template_name = 'main.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user.coach})
        return kwargs

    def form_valid(self, form):
        team_pk = form.cleaned_data['team'].pk
        return redirect('manage_team', team_pk=team_pk)
