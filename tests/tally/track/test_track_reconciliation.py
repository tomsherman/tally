"""Tests for track() reconciliation: overwrite in window, delete when missing from feed."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytz

from tally.actions.track.track import track
from tally.models.db import Config, Team, User, Activity
from tests.tally.mocks.mock_team import create_team
from tests.tally.mocks.mock_user import create_user


# Fixed "today" so the 5-day window is deterministic: 2025-02-15 in LA
# Window = [midnight Feb 10, midnight Feb 15) PST — 5 full days, today excluded
FAKE_NOW_LA = datetime(
    2025, 2, 15, 12, 0, 0, tzinfo=pytz.timezone("America/Los_Angeles")
)
# In window: Feb 12 18:00 UTC (Feb 12 10:00 PST)
IN_WINDOW_START = datetime(2025, 2, 12, 18, 0, 0, tzinfo=timezone.utc)
# On "today" (excluded): Feb 15 08:00 UTC = midnight Feb 15 PST
TODAY_START_UTC = datetime(2025, 2, 15, 8, 0, 0, tzinfo=timezone.utc)

_real_datetime = __import__("datetime").datetime
_real_timedelta = __import__("datetime").timedelta


def _patch_datetime_for_window(mock_dt):
    """Make datetime.now() return FAKE_NOW_LA and keep timedelta/combine/min real for get_start_of_day."""
    mock_dt.datetime.now.return_value = FAKE_NOW_LA
    mock_dt.timedelta = _real_timedelta
    mock_dt.datetime.combine = _real_datetime.combine
    mock_dt.datetime.min = _real_datetime.min


def _config_and_team_user(mock_db):
    """Create Config, one Team, one User; challenge start before the window."""
    config = Config(
        challenge_name="Test",
        start_date=date(2025, 2, 1),
        time_zone="America/Los_Angeles",
    )
    config.save(force_insert=True)
    team = create_team(id="team1", name="Team 1")
    team.save(force_insert=True)
    user = create_user(id="user1", name="User 1", team=team.id)
    user.save(force_insert=True)
    return config, team, user


@patch("tally.actions.track.track.backup_db")
@patch("tally.actions.track.track.get_activities")
@patch("tally.actions.track.track.StravaService")
@patch("tally.actions.track.track.datetime")
def test_track_overwrites_activity_in_reconciliation_window(
    mock_datetime_module, mock_strava_cls, mock_get_activities, mock_backup_db, mock_db
):
    """When an activity is in the 5-day window and already in DB, track() overwrites it with feed data."""
    config, team, user = _config_and_team_user(mock_db)
    _patch_datetime_for_window(mock_datetime_module)

    # Existing activity in DB with old duration
    existing = Activity(
        id="act-overwrite",
        user=user.id,
        start_time=IN_WINDOW_START,
        elapsed_seconds=3600,
        moving_seconds=1800,
        title="Morning Run",
        workout_type="Run",
    )
    existing.save(force_insert=True)

    # Feed returns same activity with updated duration (athlete corrected it)
    updated_from_feed = Activity(
        id="act-overwrite",
        user=user.id,
        start_time=IN_WINDOW_START,
        elapsed_seconds=3600,
        moving_seconds=3600,
        title="Morning Run",
        workout_type="Run",
    )
    mock_get_activities.return_value = [updated_from_feed]
    mock_strava_cls.return_value = MagicMock()

    track()

    row = Activity.get_by_id("act-overwrite")
    assert row.moving_seconds == 3600
    mock_backup_db.assert_called_once()


@patch("tally.actions.track.track.backup_db")
@patch("tally.actions.track.track.get_activities")
@patch("tally.actions.track.track.StravaService")
@patch("tally.actions.track.track.datetime")
def test_track_deletes_activity_in_window_when_not_in_feed(
    mock_datetime_module, mock_strava_cls, mock_get_activities, mock_backup_db, mock_db
):
    """When an activity is in the 5-day window but not in the feed (deleted on Strava), track() removes it."""
    config, team, user = _config_and_team_user(mock_db)
    _patch_datetime_for_window(mock_datetime_module)

    activity_in_db = Activity(
        id="act-deleted",
        user=user.id,
        start_time=IN_WINDOW_START,
        elapsed_seconds=3600,
        moving_seconds=1800,
        title="Deleted Run",
        workout_type="Run",
    )
    activity_in_db.save(force_insert=True)

    # Feed returns no activities for this team (athlete deleted the activity)
    mock_get_activities.return_value = []
    mock_strava_cls.return_value = MagicMock()

    track()

    assert Activity.get_or_none(Activity.id == "act-deleted") is None
    mock_backup_db.assert_called_once()


@patch("tally.actions.track.track.backup_db")
@patch("tally.actions.track.track.get_activities")
@patch("tally.actions.track.track.StravaService")
@patch("tally.actions.track.track.datetime")
def test_track_does_not_delete_activity_on_today_even_if_missing_from_feed(
    mock_datetime_module, mock_strava_cls, mock_get_activities, mock_backup_db, mock_db
):
    """Activity on 'today' (midnight today onward in challenge TZ) is outside the window and not deleted."""
    config, team, user = _config_and_team_user(mock_db)
    _patch_datetime_for_window(mock_datetime_module)

    # Activity at midnight Feb 15 PST (today) — outside [Feb 10, Feb 15) window
    activity_today = Activity(
        id="act-today",
        user=user.id,
        start_time=TODAY_START_UTC,
        elapsed_seconds=3600,
        moving_seconds=1800,
        title="Today Run",
        workout_type="Run",
    )
    activity_today.save(force_insert=True)

    mock_get_activities.return_value = []
    mock_strava_cls.return_value = MagicMock()

    track()

    # Should still exist: not in reconciliation window so we don't treat as "deleted on Strava"
    assert Activity.get_by_id("act-today") is not None
