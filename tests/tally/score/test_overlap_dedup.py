"""
Tests for overlapping-activity deduplication.

When multiple activities for the same user on the same day have overlapping
elapsed-time intervals, the credited time is:

    min(merged_wall_clock_seconds, sum_of_individual_active_seconds)

This prevents double-counting while never crediting more than the activities
individually warranted.
"""

import datetime

from tally.actions.score.user_active_time import get_user_active_time
from tally.actions.score.score_config import ScoreConfig
from tally.utils.activity import merge_activity_intervals
from tests.tally.mocks.mock_activity import create_activity


SCORE_CONFIG = ScoreConfig(
    score_start_date=datetime.date(2023, 1, 1),
    score_end_date=datetime.date(2023, 1, 31),
    time_zone="UTC",
)


class TestMergeActivityIntervals:
    """Unit tests for the merge_activity_intervals helper."""

    def test_single_activity(self):
        a = create_activity(
            start_time="2023-01-15T10:00:00+00:00",
            elapsed_seconds=1800,
        )
        assert merge_activity_intervals([a]) == 1800

    def test_no_overlap(self):
        a1 = create_activity(
            start_time="2023-01-15T10:00:00+00:00",
            elapsed_seconds=1800,  # 10:00-10:30
        )
        a2 = create_activity(
            start_time="2023-01-15T11:00:00+00:00",
            elapsed_seconds=1800,  # 11:00-11:30
        )
        # 30 + 30 = 60 min, no overlap
        assert merge_activity_intervals([a1, a2]) == 3600

    def test_partial_overlap(self):
        a1 = create_activity(
            start_time="2023-01-15T10:15:00+00:00",
            elapsed_seconds=1800,  # 10:15-10:45
        )
        a2 = create_activity(
            start_time="2023-01-15T10:30:00+00:00",
            elapsed_seconds=1800,  # 10:30-11:00
        )
        # Merged: 10:15-11:00 = 45 min
        assert merge_activity_intervals([a1, a2]) == 2700

    def test_full_containment(self):
        outer = create_activity(
            start_time="2023-01-15T10:00:00+00:00",
            elapsed_seconds=3600,  # 10:00-11:00
        )
        inner = create_activity(
            start_time="2023-01-15T10:15:00+00:00",
            elapsed_seconds=1800,  # 10:15-10:45
        )
        # Merged: 10:00-11:00 = 60 min
        assert merge_activity_intervals([outer, inner]) == 3600

    def test_three_activities_two_overlap(self):
        a1 = create_activity(
            start_time="2023-01-15T10:00:00+00:00",
            elapsed_seconds=1800,  # 10:00-10:30
        )
        a2 = create_activity(
            start_time="2023-01-15T10:15:00+00:00",
            elapsed_seconds=1800,  # 10:15-10:45
        )
        a3 = create_activity(
            start_time="2023-01-15T12:00:00+00:00",
            elapsed_seconds=1800,  # 12:00-12:30
        )
        # Merged: 10:00-10:45 (45 min) + 12:00-12:30 (30 min) = 75 min
        assert merge_activity_intervals([a1, a2, a3]) == 4500

    def test_empty_list(self):
        assert merge_activity_intervals([]) == 0


class TestOverlapDedup:
    """End-to-end tests through get_user_active_time."""

    def test_overlapping_runs_deduped(self, mock_db, init_users_and_teams):
        """Two overlapping runs: credit merged wall-clock, capped by sum of active."""
        run1 = create_activity(
            id="run1",
            user="user1",
            start_time="2023-01-15T10:15:00+00:00",
            elapsed_seconds=1800,  # 10:15-10:45
            moving_seconds=25 * 60,
            workout_type="Run",
        )
        run1.save(force_insert=True)
        run2 = create_activity(
            id="run2",
            user="user1",
            start_time="2023-01-15T10:30:00+00:00",
            elapsed_seconds=1800,  # 10:30-11:00
            moving_seconds=28 * 60,
            workout_type="Run",
        )
        run2.save(force_insert=True)

        result = get_user_active_time([run1, run2], SCORE_CONFIG)

        assert len(result) == 1
        # merged_elapsed = 45 min = 2700, sum_active = 25+28 = 53 min = 3180
        # credit = min(2700, 3180) = 2700
        assert result[0].active_seconds == 2700

    def test_non_overlapping_runs_unchanged(self, mock_db, init_users_and_teams):
        """Two non-overlapping runs: same as sum of active (no dedup needed)."""
        run1 = create_activity(
            id="run1",
            user="user1",
            start_time="2023-01-15T10:00:00+00:00",
            elapsed_seconds=1800,  # 10:00-10:30
            moving_seconds=25 * 60,
            workout_type="Run",
        )
        run1.save(force_insert=True)
        run2 = create_activity(
            id="run2",
            user="user1",
            start_time="2023-01-15T11:00:00+00:00",
            elapsed_seconds=1800,  # 11:00-11:30
            moving_seconds=28 * 60,
            workout_type="Run",
        )
        run2.save(force_insert=True)

        result = get_user_active_time([run1, run2], SCORE_CONFIG)

        assert len(result) == 1
        # merged_elapsed = 60 min = 3600, sum_active = 25+28 = 53 min = 3180
        # credit = min(3600, 3180) = 3180
        assert result[0].active_seconds == 53 * 60

    def test_single_activity_unchanged(self, mock_db, init_users_and_teams):
        """A single activity: active_seconds equals its individual active time."""
        run = create_activity(
            id="run1",
            user="user1",
            start_time="2023-01-15T10:00:00+00:00",
            elapsed_seconds=1800,
            moving_seconds=25 * 60,
            workout_type="Run",
        )
        run.save(force_insert=True)

        result = get_user_active_time([run], SCORE_CONFIG)

        assert len(result) == 1
        # merged_elapsed = 1800, sum_active = 1500
        # credit = min(1800, 1500) = 1500
        assert result[0].active_seconds == 25 * 60

    def test_contained_activity(self, mock_db, init_users_and_teams):
        """Activity fully inside another: credit outer's elapsed (capped by sum active)."""
        outer = create_activity(
            id="outer",
            user="user1",
            start_time="2023-01-15T10:00:00+00:00",
            elapsed_seconds=3600,  # 10:00-11:00
            moving_seconds=3600,
            workout_type="Run",
        )
        outer.save(force_insert=True)
        inner = create_activity(
            id="inner",
            user="user1",
            start_time="2023-01-15T10:15:00+00:00",
            elapsed_seconds=1800,  # 10:15-10:45
            moving_seconds=1800,
            workout_type="Run",
        )
        inner.save(force_insert=True)

        result = get_user_active_time([outer, inner], SCORE_CONFIG)

        assert len(result) == 1
        # merged_elapsed = 3600 (10:00-11:00), sum_active = 3600+1800 = 5400
        # credit = min(3600, 5400) = 3600
        assert result[0].active_seconds == 3600

    def test_overlap_where_sum_active_less_than_merged(
        self, mock_db, init_users_and_teams
    ):
        """When sum of active times < merged elapsed, credit sum of active."""
        # Two overlapping yoga sessions (elapsed used, no moving_seconds)
        yoga1 = create_activity(
            id="yoga1",
            user="user1",
            start_time="2023-01-15T10:00:00+00:00",
            elapsed_seconds=600,  # 10:00-10:10 (10 min)
            moving_seconds=None,
            workout_type="Yoga",
        )
        yoga1.save(force_insert=True)
        yoga2 = create_activity(
            id="yoga2",
            user="user1",
            start_time="2023-01-15T10:05:00+00:00",
            elapsed_seconds=600,  # 10:05-10:15 (10 min)
            moving_seconds=None,
            workout_type="Yoga",
        )
        yoga2.save(force_insert=True)

        result = get_user_active_time([yoga1, yoga2], SCORE_CONFIG)

        assert len(result) == 1
        # merged_elapsed = 15 min = 900, sum_active = 10+10 = 20 min = 1200
        # credit = min(900, 1200) = 900
        assert result[0].active_seconds == 900

    def test_overlap_dedup_applies_before_daily_cap(
        self, mock_db, init_users_and_teams
    ):
        """Dedup runs first, then the daily cap is applied on top."""
        # Two overlapping 5-hour runs
        run1 = create_activity(
            id="run1",
            user="user1",
            start_time="2023-01-15T08:00:00+00:00",
            elapsed_seconds=5 * 3600,  # 08:00-13:00
            moving_seconds=5 * 3600,
            workout_type="Run",
        )
        run1.save(force_insert=True)
        run2 = create_activity(
            id="run2",
            user="user1",
            start_time="2023-01-15T12:00:00+00:00",
            elapsed_seconds=5 * 3600,  # 12:00-17:00
            moving_seconds=5 * 3600,
            workout_type="Run",
        )
        run2.save(force_insert=True)

        # Default cap is 6h (21600)
        result = get_user_active_time([run1, run2], SCORE_CONFIG)

        assert len(result) == 1
        # merged_elapsed = 08:00-17:00 = 9h = 32400, sum_active = 5h+5h = 10h = 36000
        # deduped = min(32400, 36000) = 32400
        # then capped to 21600
        assert result[0].active_seconds == 21600

    def test_many_identical_overlapping_activities(self, mock_db, init_users_and_teams):
        """Five runs at the same time: athlete gets credit for just 1 hour."""
        activities = []
        for i in range(5):
            a = create_activity(
                id=f"run{i}",
                user="user1",
                start_time="2023-01-15T10:00:00+00:00",
                elapsed_seconds=3600,  # all 10:00-11:00
                moving_seconds=3600,
                workout_type="Run",
            )
            a.save(force_insert=True)
            activities.append(a)

        no_cap = ScoreConfig(
            score_start_date=datetime.date(2023, 1, 1),
            score_end_date=datetime.date(2023, 1, 31),
            time_zone="UTC",
            max_daily_active_seconds=None,
        )
        result = get_user_active_time(activities, no_cap)

        assert len(result) == 1
        # merged_elapsed = 3600 (one interval), sum_active = 5*3600 = 18000
        # credit = min(3600, 18000) = 3600
        assert result[0].active_seconds == 3600
