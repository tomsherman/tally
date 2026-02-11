"""Tests for apply_challenge_config: JSON parsing, missing attrs, None handling."""

import json
from types import SimpleNamespace

import tally.config
from tally.config import apply_challenge_config


class TestApplyChallengeConfig:
    def test_point_thresholds_parsed_from_json_string(self):
        """When point_thresholds is a JSON string, it's parsed to a list."""
        thresholds = [{"minutes": 10, "points": 3}]
        cfg = SimpleNamespace(
            max_daily_active_seconds=3600,
            base_points_per_hour=2,
            point_thresholds=json.dumps(thresholds),
            user_streak_bonus_points=10,
            user_streak_interval_days=5,
            team_bonus_points=8,
            strava_request_interval_seconds=3,
        )

        apply_challenge_config(cfg)

        assert tally.config.POINT_THRESHOLDS == thresholds
        assert isinstance(tally.config.POINT_THRESHOLDS, list)

    def test_point_thresholds_accepted_as_list(self):
        """When point_thresholds is already a list, it's used directly."""
        thresholds = [{"minutes": 15, "points": 1}]
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=1,
            point_thresholds=thresholds,
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )

        apply_challenge_config(cfg)

        assert tally.config.POINT_THRESHOLDS is thresholds

    def test_empty_json_string_gives_empty_list(self):
        """An empty JSON string for point_thresholds results in an empty list."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=1,
            point_thresholds="",
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )

        apply_challenge_config(cfg)

        assert tally.config.POINT_THRESHOLDS == []

    def test_none_point_thresholds_gives_empty_list(self):
        """None for point_thresholds results in an empty list."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=1,
            point_thresholds=None,
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )

        apply_challenge_config(cfg)

        assert tally.config.POINT_THRESHOLDS == []

    def test_max_daily_active_seconds_none_means_no_cap(self):
        """Explicit None for max_daily_active_seconds is stored as None (no cap)."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=1,
            point_thresholds="[]",
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )

        apply_challenge_config(cfg)

        assert tally.config.MAX_DAILY_ACTIVE_SECONDS is None

    def test_max_daily_active_seconds_integer_preserved(self):
        """An integer for max_daily_active_seconds is stored as-is."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=7200,
            base_points_per_hour=1,
            point_thresholds="[]",
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )

        apply_challenge_config(cfg)

        assert tally.config.MAX_DAILY_ACTIVE_SECONDS == 7200

    def test_missing_attributes_use_defaults(self):
        """When config object lacks attributes, sensible defaults are used."""
        cfg = SimpleNamespace()  # no attributes at all

        apply_challenge_config(cfg)

        assert tally.config.MAX_DAILY_ACTIVE_SECONDS is None
        assert tally.config.BASE_POINTS_PER_HOUR == 1
        assert tally.config.POINT_THRESHOLDS == []
        assert tally.config.USER_STREAK_BONUS_POINTS == 5
        assert tally.config.USER_STREAK_INTERVAL_DAYS == 7
        assert tally.config.TEAM_BONUS_POINTS == 5
        assert tally.config.STRAVA_REQUEST_INTERVAL_SECONDS == 5
        assert tally.config.RECONCILIATION_WINDOW_DAYS == 10

    def test_all_fields_propagated(self):
        """All fields from the config object are propagated to module globals."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=9999,
            base_points_per_hour=3,
            point_thresholds=json.dumps([{"minutes": 5, "points": 1}]),
            user_streak_bonus_points=10,
            user_streak_interval_days=3,
            team_bonus_points=20,
            strava_request_interval_seconds=2,
            reconciliation_window_days=7,
        )

        apply_challenge_config(cfg)

        assert tally.config.MAX_DAILY_ACTIVE_SECONDS == 9999
        assert tally.config.BASE_POINTS_PER_HOUR == 3
        assert tally.config.POINT_THRESHOLDS == [{"minutes": 5, "points": 1}]
        assert tally.config.USER_STREAK_BONUS_POINTS == 10
        assert tally.config.USER_STREAK_INTERVAL_DAYS == 3
        assert tally.config.TEAM_BONUS_POINTS == 20
        assert tally.config.STRAVA_REQUEST_INTERVAL_SECONDS == 2
        assert tally.config.RECONCILIATION_WINDOW_DAYS == 7
