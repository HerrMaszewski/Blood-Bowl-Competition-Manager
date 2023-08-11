from django.contrib.auth import get_user_model
from .models import Coach, Race, Position, Team, RacePositionLimit
import pytest


@pytest.fixture
def client():
    """Create a Django test client."""
    from django.test import Client
    return Client()


@pytest.fixture
def registration_data():
    """Create registration data."""
    return {
        'coach_name': 'test_coach',
        'password': 'password123',
        'password2': 'password123'
    }


@pytest.fixture
def test_user(db):
    """Create a test user."""
    username = 'test_coach'
    password = 'password123'
    user = get_user_model().objects.create_user(username=username, password=password)
    return user, password


@pytest.fixture
def test_coach(test_user):
    """Create a test coach."""
    user, _ = test_user
    return Coach.objects.create(user=user, coach_name=user.username)


@pytest.fixture
def test_race(db):
    """Create a test race."""
    return Race.objects.create(race_type='HUM')


@pytest.fixture
def logged_in_client(client, test_coach):
    """Create a client with a logged in test coach."""
    username, password = test_coach.user.username, 'password123'
    client.login(username=username, password=password)
    return client


@pytest.fixture
def test_position(test_race):
    """Create a test position."""
    return Position.objects.create(
        name='Test Position',
        movement=6,
        strength=3,
        agility=3,
        armor=8,
        passing=2,
        cost=50000,
        race=test_race,
    )


@pytest.fixture
def test_team(test_coach, test_race):
    """Create a test team."""
    return Team.objects.create(coach=test_coach, race=test_race, team_name='Test Team')


@pytest.fixture
def test_race_position_limit(test_race, test_position):

    return RacePositionLimit.objects.create(race=test_race, position=test_position, max_count=4)


