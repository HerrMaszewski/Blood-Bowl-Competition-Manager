import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Coach, Race, Team, Position, RacePositionLimit, Player
from django.test import TestCase, Client
from django.contrib.auth import get_user_model


# Testy dla LoginView

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
    assert 'Niepoprawna nazwa użytkownika lub hasło' in response.content.decode()


@pytest.mark.django_db
def test_invalid_password(client):
    user = User.objects.create_user(username='testuser', password='testpass')
    Coach.objects.create(user=user)
    response = client.post('/login/', {'coach_name': 'testuser', 'password': 'wrongpass'})
    assert response.status_code == 200
    assert 'Niepoprawna nazwa użytkownika lub hasło' in response.content.decode()


@pytest.mark.django_db
def test_user_not_coach(client):
    user = User.objects.create_user(username='testuser', password='testpass')
    response = client.post('/login/', {'coach_name': 'testuser', 'password': 'testpass'})
    assert response.status_code == 200
    assert 'Niepoprawna nazwa użytkownika lub hasło' in response.content.decode()

# Testy dla RegistrationView


class RegistrationViewTest(TestCase):
    def setUp(self):
        self.data = {
            'coach_name': 'test_coach',
            'password': 'password123',
            'password2': 'password123'
        }

    def test_successful_registration(self):
        response = self.client.post(reverse('registration'), self.data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('create_team'))
        user = User.objects.get(username='test_coach')
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('password123'))

    def test_unsuccessful_registration_invalid_data(self):
        data = self.data.copy()
        data['coach_name'] = ''
        response = self.client.post(reverse('registration'), data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFormError(form, 'coach_name', 'This field is required.')

    def test_user_logged_in_after_successful_registration(self):
        response = self.client.post(reverse('registration'), self.data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('create_team'))
        user = User.objects.get(username='test_coach')
        self.assertIsNotNone(user)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)


class CreateTeamViewTest(TestCase):
    def setUp(self):
        self.username = 'test_coach'
        self.password = 'password123'
        user = get_user_model().objects.create_user(username=self.username, password=self.password)
        self.coach = Coach.objects.create(user=user, coach_name=self.username)
        self.client.login(username=self.username, password=self.password)
        self.race = Race.objects.create(race_type='HUM')

    def test_render_create_team_form(self):
        response = self.client.get(reverse('create_team'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_team.html')

    def test_successful_team_creation(self):
        data = {
            'team_name': 'Test Team',
            'race': self.race.pk,
        }
        response = self.client.post(reverse('create_team'), data)
        self.assertEqual(response.status_code, 302)
        team = Team.objects.get(team_name='Test Team')
        self.assertEqual(team.coach, self.coach)
        self.assertRedirects(response, reverse('manage_team', args=[team.pk]))

    def test_unsuccessful_team_creation(self):
        data = {
            'team_name': '',
            'race': self.race.pk,
        }
        response = self.client.post(reverse('create_team'), data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFormError(form, 'team_name', 'This field is required.')


class ManageTeamViewTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='test_coach', password='password123')
        coach = Coach.objects.create(user=user, coach_name='test_coach')
        self.race = Race.objects.create(race_type='HUM')
        self.position = Position.objects.create(
            name='Test Position',
            movement=6,
            strength=3,
            agility=3,
            armor=8,
            passing=2,
            cost=50000,
        )
        self.team = Team.objects.create(coach=coach, race=self.race, team_name='Test Team')
        self.client.login(username='test_coach', password='password123')
        RacePositionLimit.objects.create(race=self.race, position=self.position, max_count=4)  # Creating RacePositionLimit  # Creating RacePositionLimit

    def test_create_player_successful(self):
        data = {
            'name': 'Player Name',
            'number': 1,
            'position': self.position.pk,
        }
        response = self.client.post(reverse('manage_team', args=[self.team.pk]), data)
        self.assertEqual(response.status_code, 302)  # Redirects after successful creation
        player = Player.objects.get(name='Player Name')
        self.assertEqual(player.number, 1)
        self.assertEqual(player.position, self.position)
        self.assertEqual(player.player_team, self.team)

    def test_create_player_insufficient_funds(self):
        self.team.treasury = 0
        self.team.save()

        data = {
            'name': 'Player One',
            'number': 1,
            'position': self.position.pk
        }
        response = self.client.post(reverse('manage_team', kwargs={'team_pk': self.team.pk}), data)
        self.assertEqual(response.status_code, 200)  # Stays on the page as form is invalid
        self.assertContains(response, 'Insufficient funds.')

    def test_create_player_exceeding_position_limit(self):
        race_position_limit, created = RacePositionLimit.objects.get_or_create(race=self.team.race, position=self.position)
        race_position_limit.max_count = 0
        race_position_limit.save()

        player_data = {
            'name': 'Player One',
            'number': 1,
            'position': self.position.pk,
        }
        response = self.client.post(reverse('manage_team', kwargs={'team_pk': self.team.pk}), player_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Player.objects.filter(name='Player One').exists())


    def test_create_player_invalid_number(self):
        player_data = {
            'name': 'Player Four',
            'number': 17,
            'position': self.position.pk,
        }
        response = self.client.post(reverse('manage_team', kwargs={'team_pk': self.team.pk}), player_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Player.objects.filter(name='Player Four').exists())
        self.assertContains(response, 'Invalid number. Please choose a number between 1 and 16.')








