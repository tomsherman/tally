import json
from peewee import CharField, DateField, IntegerField, TextField

from .base import BaseModel

_DEFAULT_POINT_THRESHOLDS_JSON = json.dumps(
    [
        {"minutes": 30, "points": 5},
        {"minutes": 60, "points": 2},
        {"minutes": 120, "points": 1},
    ]
)


class Config(BaseModel):
    challenge_name = CharField()
    start_date = DateField()
    time_zone = CharField()
    # Scoring and tracking (set during Configure challenge)
    max_daily_active_seconds = IntegerField(
        null=True, default=6 * 60 * 60
    )  # 6 hours, null = no cap
    base_points_per_hour = IntegerField(default=1)
    point_thresholds = TextField(
        default=_DEFAULT_POINT_THRESHOLDS_JSON
    )  # JSON list of {minutes, points}
    user_streak_bonus_points = IntegerField(default=5)
    user_streak_interval_days = IntegerField(default=7)
    team_bonus_points = IntegerField(default=5)
    strava_request_interval_seconds = IntegerField(default=5)
