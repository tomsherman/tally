from tally.config import (
    BASE_POINTS_PER_HOUR,
    POINT_THRESHOLDS,
    TEAM_BONUS_POINTS,
    USER_STREAK_BONUS_POINTS,
    USER_STREAK_INTERVAL_DAYS,
)


def calculate_user_points(active_seconds: int) -> int:
    """
    Assign points for a specific day based on how long the user was active for
    that day. Points increase with active time in 30 minute/1 hour increments.
    More points are awarded towards for the first few threshold 30 minutes, 60
    minutes and 120 minutes.

    :param active_seconds: Total active time in seconds for a specific day.

    :return: Points for the specific day.
    """
    one_minute_in_seconds = 60
    one_hour_in_minutes = 60

    active_minutes = active_seconds / one_minute_in_seconds
    points = int(active_minutes // one_hour_in_minutes) * BASE_POINTS_PER_HOUR
    for threshold in POINT_THRESHOLDS:
        if active_minutes >= threshold["minutes"]:
            points += threshold["points"]
    return points


def calculate_user_bonus_points(streak: int) -> int:
    """
    Reward users with bonus points for being active every N consecutive days.

    :param streak: The number of consecutive days the user has been active.

    :return: Bonus points for the user.
    """
    return (
        USER_STREAK_BONUS_POINTS
        if streak > 0 and streak % USER_STREAK_INTERVAL_DAYS == 0
        else 0
    )


def calculate_team_bonus_points(active_user_count: int, total_user_count: int) -> int:
    """
    Reward teams with bonus points if all users in the team have been active
    for a specific day. Teams with no members do not receive bonus points.

    :param active_user_count: Number of active users in the team.
    :param total_user_count: Total number of users in the team.

    :return: Bonus points for the team.
    """
    return (
        TEAM_BONUS_POINTS
        if total_user_count > 0 and active_user_count == total_user_count
        else 0
    )
