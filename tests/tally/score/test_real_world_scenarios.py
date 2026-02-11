"""
Tests for messy real-world scoring scenarios.

These cover edge cases that arise from real Strava data: mixed activity types
in a day, activities spanning midnight, very short/long activities, missing
moving_seconds on runs, and negative/zero elapsed times.
"""

import datetime
import pytest

from tally.actions.score.user_active_time import get_user_active_time, UserActiveTime
from tally.actions.score.user_score import get_user_daily_score
from tally.actions.score.score_config import ScoreConfig
from tally.utils.activity import get_activity_active_seconds
from tests.tally.mocks.mock_activity import create_activity


SCORE_CONFIG = ScoreConfig(
    score_start_date=datetime.date(2023, 1, 1),
    score_end_date=datetime.date(2023, 1, 31),
    time_zone="America/Los_Angeles",
)


class TestMixedActivityTypesInOneDay:
    """A user does a Run, Yoga, and Ride in the same day."""

    def test_mixed_types_accumulate_correct_active_seconds(
        self, mock_db, init_users_and_teams
    ):
        # Run: moving_seconds used (it's in MOVING_TIME_ACTIVITY_TYPES)
        run = create_activity(
            id="run1",
            user="user1",
            start_time="2023-01-15T15:00:00+00:00",  # 7 AM PST
            elapsed_seconds=3600,
            moving_seconds=1800,  # 30 min moving out of 60 min elapsed
            workout_type="Run",
        )
        run.save(force_insert=True)

        # Yoga: moving_seconds is None (not a MOVING_TIME_ACTIVITY_TYPE) → elapsed used
        yoga = create_activity(
            id="yoga1",
            user="user1",
            start_time="2023-01-15T18:00:00+00:00",  # 10 AM PST
            elapsed_seconds=2700,  # 45 min
            moving_seconds=None,
            workout_type="Yoga",
        )
        yoga.save(force_insert=True)

        # Ride: moving_seconds used
        ride = create_activity(
            id="ride1",
            user="user1",
            start_time="2023-01-15T23:00:00+00:00",  # 3 PM PST
            elapsed_seconds=7200,
            moving_seconds=5400,  # 90 min moving out of 120 min elapsed
            workout_type="Ride",
        )
        ride.save(force_insert=True)

        result = get_user_active_time([run, yoga, ride], SCORE_CONFIG)

        assert len(result) == 1
        # 1800 (run moving) + 2700 (yoga elapsed) + 5400 (ride moving) = 9900
        assert result[0].active_seconds == 9900
        assert result[0].date == datetime.date(2023, 1, 15)


class TestActivitySpanningMidnight:
    """An activity started before midnight PST and ended after; which day does it land on?"""

    def test_activity_assigned_to_start_date_in_challenge_tz(
        self, mock_db, init_users_and_teams
    ):
        # 11 PM PST Jan 15 = 07:00 UTC Jan 16
        activity = create_activity(
            id="late1",
            user="user1",
            start_time="2023-01-16T07:00:00+00:00",
            elapsed_seconds=7200,  # 2 hours, ending 1 AM PST Jan 16
            moving_seconds=7200,
            workout_type="Run",
        )
        activity.save(force_insert=True)

        result = get_user_active_time([activity], SCORE_CONFIG)

        assert len(result) == 1
        # start_time in PST is Jan 15 at 11 PM → date is Jan 15
        assert result[0].date == datetime.date(2023, 1, 15)

    def test_two_activities_around_midnight_land_on_correct_days(
        self, mock_db, init_users_and_teams
    ):
        # 11:30 PM PST Jan 15 = 07:30 UTC Jan 16
        before_midnight = create_activity(
            id="before",
            user="user1",
            start_time="2023-01-16T07:30:00+00:00",
            elapsed_seconds=1800,
            workout_type="Yoga",
        )
        before_midnight.save(force_insert=True)
        # 12:30 AM PST Jan 16 = 08:30 UTC Jan 16
        after_midnight = create_activity(
            id="after",
            user="user1",
            start_time="2023-01-16T08:30:00+00:00",
            elapsed_seconds=1800,
            workout_type="Yoga",
        )
        after_midnight.save(force_insert=True)

        result = get_user_active_time([before_midnight, after_midnight], SCORE_CONFIG)

        result.sort(key=lambda x: x.date)
        assert len(result) == 2
        assert result[0].date == datetime.date(2023, 1, 15)
        assert result[0].active_seconds == 1800
        assert result[1].date == datetime.date(2023, 1, 16)
        assert result[1].active_seconds == 1800


class TestVeryShortActivity:
    """Activities under a minute — should be counted but yield 0 points."""

    def test_30_second_activity_scores_zero_points(self, mock_db, init_users_and_teams):
        activity = create_activity(
            id="short1",
            user="user1",
            start_time="2023-01-15T15:00:00+00:00",
            elapsed_seconds=30,
            moving_seconds=30,
            workout_type="Run",
        )
        activity.save(force_insert=True)

        active_times = get_user_active_time([activity], SCORE_CONFIG)
        scores = get_user_daily_score(active_times)

        assert len(scores) == 1
        assert scores[0].points == 0

    def test_multiple_short_activities_accumulate(self, mock_db, init_users_and_teams):
        """Several 10-min activities in a day should sum to 30 min → 5 points."""
        activities = []
        for i in range(3):
            a = create_activity(
                id=f"short{i}",
                user="user1",
                start_time=f"2023-01-15T{15+i}:00:00+00:00",
                elapsed_seconds=600,  # 10 min each
                moving_seconds=600,
                workout_type="Run",
            )
            a.save(force_insert=True)
            activities.append(a)

        active_times = get_user_active_time(activities, SCORE_CONFIG)
        scores = get_user_daily_score(active_times)

        assert len(scores) == 1
        assert active_times[0].active_seconds == 1800  # 30 min total
        assert scores[0].points == 5


class TestVeryLongActivity:
    """12+ hour activity — should be capped by daily max."""

    def test_twelve_hour_activity_capped(self, mock_db, init_users_and_teams):
        twelve_hours = 12 * 3600
        activity = create_activity(
            id="long1",
            user="user1",
            start_time="2023-01-15T08:00:00+00:00",
            elapsed_seconds=twelve_hours,
            moving_seconds=twelve_hours,
            workout_type="Run",
        )
        activity.save(force_insert=True)

        # Default cap is 6 hours (21600)
        active_times = get_user_active_time([activity], SCORE_CONFIG)

        assert len(active_times) == 1
        assert active_times[0].active_seconds == 21600  # capped at 6h

    def test_twelve_hour_activity_uncapped_when_no_limit(
        self, mock_db, init_users_and_teams
    ):
        twelve_hours = 12 * 3600
        activity = create_activity(
            id="long1",
            user="user1",
            start_time="2023-01-15T08:00:00+00:00",
            elapsed_seconds=twelve_hours,
            moving_seconds=twelve_hours,
            workout_type="Run",
        )
        activity.save(force_insert=True)

        no_cap_config = ScoreConfig(
            score_start_date=datetime.date(2023, 1, 1),
            score_end_date=datetime.date(2023, 1, 31),
            time_zone="America/Los_Angeles",
            max_daily_active_seconds=None,
        )
        active_times = get_user_active_time([activity], no_cap_config)

        assert len(active_times) == 1
        assert active_times[0].active_seconds == twelve_hours


class TestMovingSecondsNullOnRun:
    """
    A Run where moving_seconds is None (e.g. manual entry, or Strava failed to
    compute it). Since Run is a MOVING_TIME_ACTIVITY_TYPE, the code checks for
    None and falls back to elapsed_seconds.
    """

    def test_run_with_none_moving_seconds_uses_elapsed(self):
        activity = create_activity(
            elapsed_seconds=3600,
            moving_seconds=None,
            workout_type="Run",
        )
        assert get_activity_active_seconds(activity) == 3600

    def test_run_with_zero_moving_seconds_uses_zero(self):
        """
        A Run with moving_seconds == 0 — the value is not None, so
        it's used as-is. This can happen with indoor activities where
        GPS jitter produces 0 moving time.
        """
        activity = create_activity(
            elapsed_seconds=3600,
            moving_seconds=0,
            workout_type="Run",
        )
        assert get_activity_active_seconds(activity) == 0

    def test_walk_with_none_moving_seconds_uses_elapsed(self):
        activity = create_activity(
            elapsed_seconds=2700,
            moving_seconds=None,
            workout_type="Walk",
        )
        assert get_activity_active_seconds(activity) == 2700

    def test_yoga_ignores_moving_seconds_entirely(self):
        """Yoga is not in MOVING_TIME_ACTIVITY_TYPES; always uses elapsed."""
        activity = create_activity(
            elapsed_seconds=3600,
            moving_seconds=100,
            workout_type="Yoga",
        )
        assert get_activity_active_seconds(activity) == 3600


class TestZeroElapsedSeconds:
    """Activity with 0 elapsed — should produce 0 active seconds and 0 points."""

    def test_zero_elapsed_activity_scores_zero(self, mock_db, init_users_and_teams):
        from tally.models.db import Activity

        # Build directly to avoid create_activity's `or 3600` default for 0
        activity = Activity(
            id="zero1",
            user="user1",
            start_time="2023-01-15T15:00:00+00:00",
            elapsed_seconds=0,
            moving_seconds=None,
            title="Zero-length Yoga",
            workout_type="Yoga",
        )
        activity.save(force_insert=True)

        active_times = get_user_active_time([activity], SCORE_CONFIG)
        scores = get_user_daily_score(active_times)

        assert len(scores) == 1
        assert active_times[0].active_seconds == 0
        assert scores[0].points == 0


class TestMovingSecondsZeroOnRunScoring:
    """
    End-to-end: a Run where moving_seconds is 0 (indoor GPS jitter).
    The athlete did 1 hour on a treadmill but Strava reports 0 moving time.
    Currently, moving_seconds is preferred for Runs when non-None, so
    the athlete gets 0 credit. This is a known limitation.
    """

    def test_zero_moving_run_gets_zero_active_seconds(
        self, mock_db, init_users_and_teams
    ):
        activity = create_activity(
            id="treadmill1",
            user="user1",
            start_time="2023-01-15T15:00:00+00:00",
            elapsed_seconds=3600,
            moving_seconds=0,
            workout_type="Run",
        )
        activity.save(force_insert=True)

        active_times = get_user_active_time([activity], SCORE_CONFIG)
        scores = get_user_daily_score(active_times)

        assert len(scores) == 1
        # This is the current behavior — 0 moving → 0 active → 0 points.
        # The athlete would need to use the Load/import flow to correct this.
        assert active_times[0].active_seconds == 0
        assert scores[0].points == 0


class TestStatPositionVariation:
    """
    In the club feed, the time stat can appear in stat_one, stat_two, or
    stat_three. get_moving_seconds_from_stats iterates all stats and picks
    the first one containing hour/minute/second HTML.
    """

    def test_time_in_stat_three_parsed_correctly(self):
        """The Ride fixture has time in stat_three — verify it's found."""
        from tally.actions.track.activity import get_moving_seconds_from_stats
        from tally.models.validation.club_feed import ActivityStatsEntry

        stats = [
            ActivityStatsEntry(
                key="stat_one",
                value="0.34<abbr class='unit' title='kilometers'> km</abbr>",
            ),
            ActivityStatsEntry(key="stat_one_subtitle", value="Distance"),
            ActivityStatsEntry(
                key="stat_two",
                value="12<abbr class='unit' title='meters'> m</abbr>",
            ),
            ActivityStatsEntry(key="stat_two_subtitle", value="Elev Gain"),
            ActivityStatsEntry(
                key="stat_three",
                value="11<abbr class='unit' title='minute'>m</abbr> 12<abbr class='unit' title='second'>s</abbr>",
            ),
            ActivityStatsEntry(key="stat_three_subtitle", value="Time"),
        ]

        result = get_moving_seconds_from_stats(stats)
        assert result == 11 * 60 + 12  # 672 seconds

    def test_time_in_stat_one_with_no_distance(self):
        """Pilates fixture: time is stat_one, no distance stat at all."""
        from tally.actions.track.activity import get_moving_seconds_from_stats
        from tally.models.validation.club_feed import ActivityStatsEntry

        stats = [
            ActivityStatsEntry(
                key="stat_one",
                value="30<abbr class='unit' title='minute'>m</abbr> 28<abbr class='unit' title='second'>s</abbr>",
            ),
            ActivityStatsEntry(key="stat_one_subtitle", value="Time"),
            ActivityStatsEntry(
                key="stat_two",
                value="99<abbr class='unit' title='beats per minute'> bpm</abbr>",
            ),
            ActivityStatsEntry(key="stat_two_subtitle", value="Avg HR"),
        ]

        result = get_moving_seconds_from_stats(stats)
        assert result == 30 * 60 + 28  # 1828 seconds

    def test_no_time_stat_at_all_returns_none(self):
        """An activity with only distance, elevation, pace — no time unit."""
        from tally.actions.track.activity import get_moving_seconds_from_stats
        from tally.models.validation.club_feed import ActivityStatsEntry

        stats = [
            ActivityStatsEntry(
                key="stat_one",
                value="5.2<abbr class='unit' title='kilometers'> km</abbr>",
            ),
            ActivityStatsEntry(
                key="stat_two",
                value="100<abbr class='unit' title='meters'> m</abbr>",
            ),
            ActivityStatsEntry(
                key="stat_three",
                value="4:30<abbr class='unit' title='per kilometer'> /km</abbr>",
            ),
        ]

        result = get_moving_seconds_from_stats(stats)
        assert result is None
