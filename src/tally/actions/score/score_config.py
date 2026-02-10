import datetime
from typing import Any

import tally.config

_UNSET: Any = object()  # sentinel for "use config value"


class ScoreConfig:
    def __init__(
        self,
        score_start_date: datetime.date,
        score_end_date: datetime.date,
        time_zone: str,
        max_daily_active_seconds: int | None = _UNSET,
    ):
        self.score_start_date = score_start_date
        self.score_end_date = score_end_date
        self.time_zone = time_zone
        self.max_daily_active_seconds = (
            tally.config.MAX_DAILY_ACTIVE_SECONDS
            if max_daily_active_seconds is _UNSET
            else max_daily_active_seconds
        )
