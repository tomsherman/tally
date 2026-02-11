"""Tests that the point system respects non-default config values."""

import json
from types import SimpleNamespace

import tally.config
from tally.config import apply_challenge_config
from tally.actions.score.point_system import (
    calculate_user_points,
    calculate_user_bonus_points,
    calculate_team_bonus_points,
)


def _apply_and_restore(cfg):
    """Apply a custom config and return a cleanup function that restores the previous config."""
    prev = SimpleNamespace(
        max_daily_active_seconds=tally.config.MAX_DAILY_ACTIVE_SECONDS,
        base_points_per_hour=tally.config.BASE_POINTS_PER_HOUR,
        point_thresholds=tally.config.POINT_THRESHOLDS,
        user_streak_bonus_points=tally.config.USER_STREAK_BONUS_POINTS,
        user_streak_interval_days=tally.config.USER_STREAK_INTERVAL_DAYS,
        team_bonus_points=tally.config.TEAM_BONUS_POINTS,
        strava_request_interval_seconds=tally.config.STRAVA_REQUEST_INTERVAL_SECONDS,
    )
    apply_challenge_config(cfg)
    return prev


class TestCalculateUserPointsCustomConfig:
    def test_different_base_points_per_hour(self):
        """With base_points_per_hour=3, 1 hour earns 3 base + threshold bonuses."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=3,
            point_thresholds=json.dumps(
                [{"minutes": 30, "points": 5}, {"minutes": 60, "points": 2}]
            ),
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )
        prev = _apply_and_restore(cfg)
        try:
            # 60 min: 1 hour * 3 base + 5 (30 min) + 2 (60 min) = 10
            assert calculate_user_points(60 * 60) == 10
            # 120 min: 2 hours * 3 base + 5 + 2 = 13
            assert calculate_user_points(120 * 60) == 13
        finally:
            apply_challenge_config(prev)

    def test_different_thresholds(self):
        """Custom thresholds change which bonuses are awarded."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=1,
            point_thresholds=json.dumps([{"minutes": 10, "points": 2}]),
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )
        prev = _apply_and_restore(cfg)
        try:
            # 10 min: 0 base hours + 2 (threshold) = 2
            assert calculate_user_points(10 * 60) == 2
            # 60 min: 1 base + 2 (threshold) = 3
            assert calculate_user_points(60 * 60) == 3
            # 5 min: below threshold, 0
            assert calculate_user_points(5 * 60) == 0
        finally:
            apply_challenge_config(prev)

    def test_empty_thresholds_only_base_points(self):
        """With no thresholds, only base points per hour are awarded."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=2,
            point_thresholds="[]",
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )
        prev = _apply_and_restore(cfg)
        try:
            assert calculate_user_points(30 * 60) == 0  # <1 hour, 0 base
            assert calculate_user_points(60 * 60) == 2  # 1 hour * 2
            assert calculate_user_points(120 * 60) == 4  # 2 hours * 2
        finally:
            apply_challenge_config(prev)


class TestCalculateUserBonusPointsCustomConfig:
    def test_custom_streak_interval_and_bonus(self):
        """With interval=3 and bonus=10, streak of 3 earns 10 pts."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=1,
            point_thresholds="[]",
            user_streak_bonus_points=10,
            user_streak_interval_days=3,
            team_bonus_points=5,
            strava_request_interval_seconds=5,
        )
        prev = _apply_and_restore(cfg)
        try:
            assert calculate_user_bonus_points(3) == 10
            assert calculate_user_bonus_points(6) == 10
            assert calculate_user_bonus_points(7) == 0  # not multiple of 3
            assert calculate_user_bonus_points(2) == 0
        finally:
            apply_challenge_config(prev)


class TestCalculateTeamBonusPointsCustomConfig:
    def test_custom_team_bonus(self):
        """With team_bonus_points=15, full team activity earns 15."""
        cfg = SimpleNamespace(
            max_daily_active_seconds=None,
            base_points_per_hour=1,
            point_thresholds="[]",
            user_streak_bonus_points=5,
            user_streak_interval_days=7,
            team_bonus_points=15,
            strava_request_interval_seconds=5,
        )
        prev = _apply_and_restore(cfg)
        try:
            assert calculate_team_bonus_points(3, 3) == 15
            assert calculate_team_bonus_points(2, 3) == 0
        finally:
            apply_challenge_config(prev)
