"""
Central configuration for Tally. Edit this file to change scoring rules,
daily caps, and tracking behaviour.
"""

# -----------------------------------------------------------------------------
# Daily activity cap
# -----------------------------------------------------------------------------
# Maximum active seconds credited per person per day. Activity beyond this
# is ignored for scoring. Set to None to disable the cap.
MAX_DAILY_ACTIVE_SECONDS = 6 * 60 * 60  # 6 hours

# -----------------------------------------------------------------------------
# User points (base and thresholds)
# -----------------------------------------------------------------------------
# Base points: 1 point per full hour of active time.
BASE_POINTS_PER_HOUR = 1

# Additional bonus points at time thresholds (minutes, points).
# A user receives the bonus for each threshold they meet or exceed.
POINT_THRESHOLDS = [
    {"minutes": 30, "points": 5},
    {"minutes": 60, "points": 2},
    {"minutes": 120, "points": 1},
]

# -----------------------------------------------------------------------------
# User streak bonus
# -----------------------------------------------------------------------------
# Bonus points awarded for every N consecutive days with at least 1 point.
USER_STREAK_BONUS_POINTS = 5
USER_STREAK_INTERVAL_DAYS = 7

# -----------------------------------------------------------------------------
# Team bonus
# -----------------------------------------------------------------------------
# Bonus points awarded to the team when all members earn at least 1 point that day.
TEAM_BONUS_POINTS = 5

# -----------------------------------------------------------------------------
# Strava / tracking
# -----------------------------------------------------------------------------
# Seconds to wait between Strava API requests (rate limiting).
STRAVA_REQUEST_INTERVAL_SECONDS = 5
