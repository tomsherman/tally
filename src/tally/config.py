"""
Configuration loaded from a required config.yaml file. No defaults are
compiled in; all values must be provided in the YAML file.
"""

import sys
from pathlib import Path

# Set after load_from_file(); consumed by score_config, point_system, activity
MAX_DAILY_ACTIVE_SECONDS = None
BASE_POINTS_PER_HOUR = None
POINT_THRESHOLDS = None
USER_STREAK_BONUS_POINTS = None
USER_STREAK_INTERVAL_DAYS = None
TEAM_BONUS_POINTS = None
STRAVA_REQUEST_INTERVAL_SECONDS = None

_REQUIRED_KEYS = [
    "base_points_per_hour",
    "point_thresholds",
    "user_streak_bonus_points",
    "user_streak_interval_days",
    "team_bonus_points",
    "strava_request_interval_seconds",
]


def load_from_file(path: str | Path) -> None:
    """Load configuration from a YAML file. Required when running as executable."""
    import yaml

    global MAX_DAILY_ACTIVE_SECONDS, BASE_POINTS_PER_HOUR, POINT_THRESHOLDS
    global USER_STREAK_BONUS_POINTS, USER_STREAK_INTERVAL_DAYS, TEAM_BONUS_POINTS
    global STRAVA_REQUEST_INTERVAL_SECONDS

    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Config YAML must be a mapping (key-value) at the top level")

    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(
            f"Config file missing required keys: {', '.join(missing)}. "
            f"See config.example.yaml for the expected format."
        )

    # max_daily_active_seconds is optional (omit or null = no cap)
    MAX_DAILY_ACTIVE_SECONDS = data.get("max_daily_active_seconds")

    BASE_POINTS_PER_HOUR = int(data["base_points_per_hour"])
    raw_thresholds = data["point_thresholds"]
    if not isinstance(raw_thresholds, list) or not raw_thresholds:
        raise ValueError(
            "point_thresholds must be a non-empty list of {minutes, points}"
        )
    POINT_THRESHOLDS = [
        {"minutes": int(t["minutes"]), "points": int(t["points"])}
        for t in raw_thresholds
    ]
    USER_STREAK_BONUS_POINTS = int(data["user_streak_bonus_points"])
    USER_STREAK_INTERVAL_DAYS = int(data["user_streak_interval_days"])
    TEAM_BONUS_POINTS = int(data["team_bonus_points"])
    STRAVA_REQUEST_INTERVAL_SECONDS = int(data["strava_request_interval_seconds"])

    # Write into module globals (cannot assign to global name in one line and use it)
    mod = sys.modules[__name__]
    mod.MAX_DAILY_ACTIVE_SECONDS = MAX_DAILY_ACTIVE_SECONDS
    mod.BASE_POINTS_PER_HOUR = BASE_POINTS_PER_HOUR
    mod.POINT_THRESHOLDS = POINT_THRESHOLDS
    mod.USER_STREAK_BONUS_POINTS = USER_STREAK_BONUS_POINTS
    mod.USER_STREAK_INTERVAL_DAYS = USER_STREAK_INTERVAL_DAYS
    mod.TEAM_BONUS_POINTS = TEAM_BONUS_POINTS
    mod.STRAVA_REQUEST_INTERVAL_SECONDS = STRAVA_REQUEST_INTERVAL_SECONDS
