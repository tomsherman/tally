import datetime
from typing import List, Tuple
import pytz

from tally.models.db import Activity, User
from tally.actions.score.score_config import ScoreConfig
from tally.utils.activity import get_activity_active_seconds, merge_activity_intervals


class UserActiveTime:
    def __init__(self, user: User, date: datetime.date, active_seconds: int = 0):
        self.user = user
        self.date = date
        self.active_seconds = active_seconds

    def __str__(self):
        return (
            f"UserActiveTime("
            f"user={self.user.id}, "
            f"date={self.date}, "
            f"active_seconds={self.active_seconds})"
        )

    def __repr__(self):
        return self.__str__()


def get_user_active_time(
    activities: List[Activity], config: ScoreConfig
) -> List[UserActiveTime]:
    # Collect activities per (user, date) group
    activity_groups = dict[Tuple[str, datetime.date], Tuple[User, List[Activity]]]()

    for activity in activities:
        activity_date = (
            datetime.datetime.fromisoformat(activity.start_time)
            .astimezone(pytz.timezone(config.time_zone))
            .date()
        )
        if (
            activity_date > config.score_end_date
            or activity_date < config.score_start_date
        ):
            continue

        key = (activity.user.id, activity_date)
        if key not in activity_groups:
            activity_groups[key] = (activity.user, [])
        activity_groups[key][1].append(activity)

    result: List[UserActiveTime] = []
    for (user_id, date), (user, group_activities) in activity_groups.items():
        sum_active = sum(get_activity_active_seconds(a) for a in group_activities)
        merged_elapsed = merge_activity_intervals(group_activities)
        active_seconds = min(merged_elapsed, sum_active)
        result.append(UserActiveTime(user, date, active_seconds))

    if config.max_daily_active_seconds is not None:
        for active_time in result:
            active_time.active_seconds = min(
                active_time.active_seconds, config.max_daily_active_seconds
            )

    return result
