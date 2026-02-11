from tally.models.db import Activity


# Activity types for which we trust Strava's "moving time" over elapsed time.
#
# Background — Strava reports two durations for every activity:
#   elapsed_time  – wall‑clock time from start to finish, including pauses.
#   moving_time   – time the athlete was actually moving, derived from GPS
#                   speed data with an auto‑pause threshold.
#
# For GPS‑tracked outdoor activities (Run, Walk, Ride, Hike, EBikeRide),
# moving time is the better measure of effort because it strips out idle
# time when the athlete stopped at a traffic light, took a photo, etc.
#
# For non‑GPS / stationary activities (Yoga, Pilates, Swim, WeightTraining,
# etc.) Strava does not compute a meaningful moving time.  The club feed
# may still show a "Time" stat, but it reflects elapsed time, so we use
# elapsed_seconds directly for those types.
#
# Edge cases:
#   • Manual entries often have no moving time in the feed stats, so
#     moving_seconds will be None.  We fall back to elapsed_seconds.
#   • Indoor GPS‑tracked activities (treadmill with GPS on) can have
#     unreliable moving time due to GPS jitter (e.g. 0 seconds for a
#     30‑minute run).  Because moving_seconds is non‑None, we still use
#     it — the athlete should correct the activity via the Load/import
#     flow if this happens.
MOVING_TIME_ACTIVITY_TYPES = ["Walk", "Run", "EBikeRide", "Ride", "Hike"]


def get_activity_active_seconds(activity: Activity) -> int:
    """
    Return the number of seconds that count toward scoring for this activity.

    For activity types in MOVING_TIME_ACTIVITY_TYPES, we prefer
    ``moving_seconds`` (Strava's auto‑pause‑adjusted time) when available.
    For all other types, or when ``moving_seconds`` is None, we use
    ``elapsed_seconds`` (the full wall‑clock duration reported by Strava).
    """

    if (
        activity.workout_type in MOVING_TIME_ACTIVITY_TYPES
        and activity.moving_seconds is not None
    ):
        return activity.moving_seconds
    return activity.elapsed_seconds


def get_activity_link(activity: Activity) -> str:
    return f"https://www.strava.com/activities/{activity.id}"
