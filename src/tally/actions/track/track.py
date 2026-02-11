import logging
from typing import List
import datetime

import pytz

import tally.config
from tally.models.db import Config, Team, User, Activity
from tally.actions.track.activity import get_activities
from tally.services.strava import StravaService
from tally.utils.date import get_start_of_day
from tally.services.db import backup_db


logger = logging.getLogger(__name__)


def track():
    config: Config | None = Config.select().first()
    if not config:
        print(
            "No active challenge found. Start a new challenge first. Cancelling operation."
        )
        return

    tally.config.apply_challenge_config(config)
    challenge_start_time = get_start_of_day(config.start_date, config.time_zone)
    tz = pytz.timezone(config.time_zone)
    today = datetime.datetime.now(tz).date()
    # Window: [midnight (today - N days), midnight today) in challenge TZ — N full days, today excluded
    window_start = get_start_of_day(
        today - datetime.timedelta(days=tally.config.RECONCILIATION_WINDOW_DAYS),
        config.time_zone,
    )
    window_end = get_start_of_day(today, config.time_zone)
    window_start_utc = window_start.astimezone(pytz.UTC)
    window_end_utc = window_end.astimezone(pytz.UTC)

    # Avoid fetching already saved activities
    last_activity: Activity | None = (
        Activity.select().order_by(Activity.start_time.desc()).first()
    )
    last_tracked_time = (
        datetime.datetime.fromisoformat(last_activity.start_time)
        if last_activity
        else challenge_start_time
    )

    teams: List[Team] = Team.select()
    activities: List[Activity] = []
    feed_activity_ids_by_team: dict = {}
    print("Please wait, a browser window is opening...")
    strava_service = StravaService()
    strava_service.login()
    for team in teams:
        print(f"Fetching activities for team {team.id}")
        team_activities = get_activities(strava_service, team, last_tracked_time)
        feed_activity_ids_by_team[team.id] = {a.id for a in team_activities}
        activities.extend(team_activities)
        print(f"Fetched {len(team_activities)} activities for team {team.id}")

    saved_activity_count = 0
    for activity in activities:
        # Drop activities that occurred before the challenge started
        if activity.start_time < challenge_start_time:
            continue

        in_window = window_start_utc <= activity.start_time < window_end_utc
        existing = (
            Activity.get_or_none(Activity.id == activity.id) if in_window else None
        )
        if in_window and existing:
            Activity.replace(**activity.__data__).execute()
        else:
            Activity.insert(**activity.__data__).on_conflict_ignore().execute()

        logger.debug(f"Saved {activity}")
        saved_activity_count += 1

    # Remove activities that are in the reconciliation window but no longer in the feed (deleted on Strava)
    deleted_count = 0
    for act in (
        Activity.select()
        .join(User)
        .where(
            Activity.start_time >= window_start_utc,
            Activity.start_time < window_end_utc,
        )
    ):
        if act.id not in feed_activity_ids_by_team.get(act.user.team_id, set()):
            act.delete_instance()
            deleted_count += 1

    msg = f"Saved {saved_activity_count} activities after {last_tracked_time}"
    if deleted_count:
        msg += f"; removed {deleted_count} activity/activities no longer in feed"
    print(msg)

    backup_db()
