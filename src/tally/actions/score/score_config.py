import datetime

from tally.config import MAX_DAILY_ACTIVE_SECONDS


class ScoreConfig:
    def __init__(
        self,
        score_start_date: datetime.date,
        score_end_date: datetime.date,
        time_zone: str,
        max_daily_active_seconds: int | None = MAX_DAILY_ACTIVE_SECONDS,
    ):
        self.score_start_date = score_start_date
        self.score_end_date = score_end_date
        self.time_zone = time_zone
        self.max_daily_active_seconds = max_daily_active_seconds
