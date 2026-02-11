import json
from pathlib import Path

import yaml

from tally.config import apply_challenge_config
from tests.tally.mocks.mock_db import mock_db


def _load_test_config():
    path = Path(__file__).resolve().parent / "tests" / "tally" / "fixtures" / "config.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # Build an object with the same attributes as DB Config so apply_challenge_config works
    class _TestConfig:
        pass

    c = _TestConfig()
    c.max_daily_active_seconds = data.get("max_daily_active_seconds")
    c.base_points_per_hour = data["base_points_per_hour"]
    c.point_thresholds = (
        json.dumps(data["point_thresholds"])
        if isinstance(data["point_thresholds"], list)
        else data["point_thresholds"]
    )
    c.user_streak_bonus_points = data["user_streak_bonus_points"]
    c.user_streak_interval_days = data["user_streak_interval_days"]
    c.team_bonus_points = data["team_bonus_points"]
    c.strava_request_interval_seconds = data["strava_request_interval_seconds"]
    c.reconciliation_window_days = data["reconciliation_window_days"]
    return c


apply_challenge_config(_load_test_config())
