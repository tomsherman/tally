"""
Runtime configuration taken from the current challenge (DB Config).
Set via apply_challenge_config() at the start of score() and track().
"""

import json

# Set after apply_challenge_config(); consumed by score_config, point_system, activity
MAX_DAILY_ACTIVE_SECONDS = None
BASE_POINTS_PER_HOUR = None
POINT_THRESHOLDS = None
USER_STREAK_BONUS_POINTS = None
USER_STREAK_INTERVAL_DAYS = None
TEAM_BONUS_POINTS = None
STRAVA_REQUEST_INTERVAL_SECONDS = None
RECONCILIATION_WINDOW_DAYS = None


def apply_challenge_config(config) -> None:
    """Load scoring and tracking settings from the challenge config (DB)."""
    global MAX_DAILY_ACTIVE_SECONDS, BASE_POINTS_PER_HOUR, POINT_THRESHOLDS
    global USER_STREAK_BONUS_POINTS, USER_STREAK_INTERVAL_DAYS, TEAM_BONUS_POINTS
    global STRAVA_REQUEST_INTERVAL_SECONDS, RECONCILIATION_WINDOW_DAYS

    MAX_DAILY_ACTIVE_SECONDS = getattr(config, "max_daily_active_seconds", None)
    BASE_POINTS_PER_HOUR = getattr(config, "base_points_per_hour", 1)
    raw = getattr(config, "point_thresholds", None)
    if isinstance(raw, str):
        POINT_THRESHOLDS = json.loads(raw) if raw else []
    else:
        POINT_THRESHOLDS = raw or []
    USER_STREAK_BONUS_POINTS = getattr(config, "user_streak_bonus_points", 5)
    USER_STREAK_INTERVAL_DAYS = getattr(config, "user_streak_interval_days", 7)
    TEAM_BONUS_POINTS = getattr(config, "team_bonus_points", 5)
    STRAVA_REQUEST_INTERVAL_SECONDS = getattr(
        config, "strava_request_interval_seconds", 5
    )
    RECONCILIATION_WINDOW_DAYS = getattr(config, "reconciliation_window_days", 10)
