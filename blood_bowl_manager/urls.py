"""
URL configuration for blood_bowl_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from bbm_app.views import MainPageView, LoginView, RegistrationView, CreateTeamView, ManageTeamView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', MainPageView.as_view(), name='main'),
    path('login/', LoginView.as_view(), name='login'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('team_creation/', CreateTeamView.as_view(), name='create_team'),
    path('manage_team/<int:team_id>/', ManageTeamView.as_view(), name='manage_team'),
]
