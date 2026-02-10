import pytest

from tests.tally.mocks.mock_team import create_team
from tests.tally.mocks.mock_user import create_user


@pytest.fixture
def init_users_and_teams(mock_db):
    """One team with two users (used by user active time and user daily score tests)."""
    team = create_team(id="team1", name="Test Team")
    team.save(force_insert=True)
    create_user(id="user1", name="Test User", team=team.id).save(force_insert=True)
    create_user(id="user2", name="Test User 2", team=team.id).save(force_insert=True)
    yield


@pytest.fixture
def init_teams_and_users(mock_db):
    """Multiple teams with users (used by team daily and cumulative score tests)."""
    team1 = create_team(id="team1", name="Team Alpha")
    team1.save(force_insert=True)
    team2 = create_team(id="team2", name="Team Beta")
    team2.save(force_insert=True)
    team3 = create_team(id="team3", name="Team Gamma")
    team3.save(force_insert=True)

    create_user(id="user1", name="Alice", team="team1").save(force_insert=True)
    create_user(id="user2", name="Bob", team="team1").save(force_insert=True)
    create_user(id="user3", name="Charlie", team="team2").save(force_insert=True)
    create_user(id="user4", name="Diana", team="team3").save(force_insert=True)

    yield
