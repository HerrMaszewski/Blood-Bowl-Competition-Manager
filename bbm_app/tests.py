import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Coach, Team, RacePositionLimit, Player


@pytest.mark.django_db
def test_valid_login(client):
    user = User.objects.create_user(username='testuser', password='testpass')
    Coach.objects.create(user=user)
    response = client.post('/login/', {'coach_name': 'testuser', 'password': 'testpass'})
    assert response.status_code == 302


@pytest.mark.django_db
def test_invalid_username(client):
    response = client.post('/login/', {'coach_name': 'nonexistentuser', 'password': 'testpass'})
    assert response.status_code == 200
    assert 'User does not exist' in response.content.decode()


@pytest.mark.django_db
def test_invalid_password(client):
    user = User.objects.create_user(username='testuser', password='testpass')
    Coach.objects.create(user=user)
    response = client.post('/login/', {'coach_name': 'testuser', 'password': 'wrongpass'})
    assert response.status_code == 200
    assert 'Invalid password' in response.content.decode()


@pytest.mark.django_db
def test_user_not_coach(client):
    User.objects.create_user(username='testuser', password='testpass')
    response = client.post('/login/', {'coach_name': 'testuser', 'password': 'testpass'})
    assert response.status_code == 200
    assert 'Coach does not exist' in response.content.decode()

# Testy dla RegistrationView


def test_successful_registration(client, registration_data, db):
    response = client.post(reverse('registration'), registration_data)
    assert response.status_code == 302
    assert response.url == reverse('create_team')
    user = User.objects.get(username='test_coach')
    assert user is not None
    assert user.check_password('password123')


def test_unsuccessful_registration_invalid_data(client, registration_data):
    registration_data['coach_name'] = ''
    response = client.post(reverse('registration'), registration_data)
    assert response.status_code == 200
    form = response.context['form']
    assert form.errors['coach_name'] == ['This field is required.']


def test_user_logged_in_after_successful_registration(client, registration_data, db):
    response = client.post(reverse('registration'), registration_data)
    assert response.status_code == 302
    assert response.url == reverse('create_team')
    user = User.objects.get(username='test_coach')
    assert user is not None
    assert int(client.session['_auth_user_id']) == user.pk


def test_render_create_team_form(logged_in_client):
    response = logged_in_client.get(reverse('create_team'))
    assert response.status_code == 200
    assert 'create_team.html' in [template.name for template in response.templates]


def test_successful_team_creation(logged_in_client, test_coach, test_race):
    data = {
        'team_name': 'Test Team',
        'race': test_race.pk,
    }
    response = logged_in_client.post(reverse('create_team'), data)
    assert response.status_code == 302
    team = Team.objects.get(team_name='Test Team')
    assert team.coach == test_coach
    assert response.url == reverse('manage_team', args=[team.pk])


def test_unsuccessful_team_creation(logged_in_client, test_race):
    data = {
        'team_name': '',
        'race': test_race.pk,
    }
    response = logged_in_client.post(reverse('create_team'), data)
    assert response.status_code == 200
    form = response.context['form']
    assert form.errors['team_name'] == ['This field is required.']


def test_create_player_successful(logged_in_client, test_team, test_position, test_race_position_limit):
    data = {
        'name': 'Player One',
        'number': 1,
        'position': test_position.pk,
        'submit_player': 'any_value',
    }
    response = logged_in_client.post(reverse('manage_team', args=[test_team.pk]), data)
    assert response.status_code == 200
    assert Player.objects.filter(name='Player One', number=1, position=test_position, player_team=test_team).exists()


def test_create_player_insufficient_funds(logged_in_client, test_team, test_position, test_race_position_limit):
    test_team.treasury = 0
    test_team.save()
    data = {
        'name': 'Player One',
        'number': 1,
        'position': test_position.pk,
        'submit_player': 'any_value',
    }
    response = logged_in_client.post(reverse('manage_team', kwargs={'team_pk': test_team.pk}), data)
    form = response.context['form']
    assert 'Insufficient funds.' in str(form.errors['position'])


def test_create_player_exceeding_position_limit(logged_in_client, test_race, test_position, test_team):
    RacePositionLimit.objects.get_or_create(race=test_race, position=test_position, max_count=0)
    data = {
        'name': 'Player Three',
        'number': 1,
        'position': test_position.pk,
        'submit_player': 'any_value',
    }
    response = logged_in_client.post(reverse('manage_team', kwargs={'team_pk': test_team.pk}), data)
    assert response.status_code == 200
    assert not Player.objects.filter(name='Player Three').exists()
