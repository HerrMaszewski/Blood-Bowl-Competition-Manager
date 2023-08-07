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
    """
    A view that handles user login.

    This view uses LoginForm to authenticate a user. Upon successful authentication,
    the user is logged in and redirected to the 'main' view. If authentication fails,
    the form with errors is rendered.
    """
    template_name = 'login.html'
    form_class = LoginForm
    success_url = reverse_lazy('main')

    def form_valid(self, form):
        """
        Handles the submission of a valid form.

        This method logs in the user associated with the form and redirects to the
        success URL.
        """
        login(self.request, form.user)
        return super().form_valid(form)


class LogoutView(LogoutView):
    """
    A view that handles user logout.

    Upon logout, the user is redirected to the 'login' view.
    """
    next_page = reverse_lazy('login')


class RegistrationView(FormView):
    """
    A view that handles user registration.

    Upon successful form validation and user registration,
    the user is logged in and redirected to the 'create_team' view.
    """
    template_name = 'registration.html'
    form_class = CreateCoachForm
    success_url = reverse_lazy('create_team')

    def form_valid(self, form):
        """
        This method is called if the form is valid.

        It creates a coach, logs them in, and then redirects to the create team page.
        """
        coach = form.save()
        username = form.cleaned_data.get('coach_name')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
        return super().form_valid(form)


class CreateTeamView(LoginRequiredMixin, FormView):
    """
    This is a Django FormView that is used for creating a new team.
    It requires that a user is logged in to access it (hence LoginRequiredMixin),
    and uses the CreateTeamForm for data submission.
    The page that is rendered with this view uses the template 'create_team.html'.
    """
    form_class = CreateTeamForm
    template_name = 'create_team.html'

    def form_valid(self, form):
        """
        This method is called when the form is valid.

        It creates a new team, associates it with the current user (who is a coach),
        sets the chosen race, saves the team, and then redirects to the manage team page for the newly created team.
        """
        team = form.save(commit=False)
        team.coach = Coach.objects.get(user=self.request.user)
        team.race = form.cleaned_data['race']
        team.save()
        team.refresh_from_db()

        return redirect('manage_team', team_pk=team.pk)


class ManageTeamView(LoginRequiredMixin, FormView):
    """
    This view is used to manage a specific team.
    It requires a user to be logged in, and it uses the FormView Django class for form handling.
    The page that is rendered with this view uses the template 'manage_team.html'.
    """
    template_name = "manage_team.html"

    def dispatch(self, request, *args, **kwargs):
        """
        This method is run before handling the request.

        It fetches the team based on the passed team id.
        If the team does not exist or the logged-in user is not the coach of the team, it denies the request.
        """
        self.team = get_object_or_404(Team, pk=kwargs['team_pk'])
        if self.team.coach.user != request.user:
            return HttpResponseForbidden('You are not allowed to modify this team.')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        This method handles GET requests.

        It prepares the form and the players data for the team, and renders the page with these data.
        """
        add_player_form = AddPlayerForm(team=self.team)
        players = self.team.players.order_by('number')
        return render(request, self.template_name, {'team': self.team, 'add_player_form': add_player_form, 'players': players})

    def post(self, request, *args, **kwargs):
        """
        This method handles POST requests.

        It checks which type of action was submitted in the form, and depending on the action,
        it either adds a reroll, an apothecary, an assistant coach, a cheerleader to the team,
        or creates a new player in the team.

        In all cases where the team is modified, the team's treasury is deducted by the respective cost of the action.

        At the end, it renders the page with the updated team data and the form for adding a new player.
        """
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
    """
    This is a view class for the main page of the application.

    The page requires the user to be logged in. If the user is logged in, the page displays a form for selecting a team.
    """
    template_name = 'main.html'

    def get(self, request, *args, **kwargs):
        """
        This method handles GET requests.

        It renders the main page with the form for selecting a team.
        """
        select_team_form = SelectTeamForm(user=request.user.coach)
        return render(request, self.template_name, {'select_team_form': select_team_form})


class SelectTeamView(LoginRequiredMixin, FormView):
    """
    This is a view class for the select team form on the main page of the application.

    The view requires the user to be logged in. If the user is logged in, and a team is selected via the form,
    the user is redirected to the manage team page of the selected team.
    """
    form_class = SelectTeamForm
    template_name = 'main.html'

    def get_form_kwargs(self):
        """
        This method returns the keyword arguments for instantiating the form.

        In this case, it adds the currently logged in user's coach instance to the arguments.
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user.coach})
        return kwargs

    def form_valid(self, form):
        """
        This method is called if the form is valid.

        It redirects the user to the manage team page of the selected team.
        """
        team_pk = form.cleaned_data['team'].pk
        return redirect('manage_team', team_pk=team_pk)
