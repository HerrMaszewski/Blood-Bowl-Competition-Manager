from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views import View

from .forms import LoginForm, CreateCoachForm


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
    success_url = reverse_lazy('main')

    def form_valid(self, form):
        coach = form.save()
        username = form.cleaned_data.get('coach_name')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
        return super().form_valid(form)


class MainPageView(View):
    pass
