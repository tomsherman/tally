from typing import List
import logging
import questionary
from pytz import common_timezones
import traceback

from tally.utils.date import prompt_date
from tally.actions.initialize.user_list import (
    parse_user_list,
    UserRow,
)
from tally.actions.initialize.create_tables import create_tables
from tally.models.db import Config, User, Team
from tally.services.db import backup_db
from tally.utils.file import prompt_select_file, FileType


logger = logging.getLogger(__name__)


def create_teams(user_list: List[UserRow]) -> List[str]:
    team_ids = set()
    for user_row in user_list:
        if user_row.team_id in team_ids:
            logger.debug(f"Skipping duplicate team creation for ID: {user_row.team_id}")
            continue

        team = Team(
            id=user_row.team_id,
            name=user_row.team_name,
        )
        Team.replace(**team.__data__).execute()

        print(f"Created {team}")
        team_ids.add(user_row.team_id)
    return list(team_ids)


def create_users(user_list: List[UserRow]) -> List[str]:
    user_ids = set()
    for user_row in user_list:
        user_id = user_row.get_user_id()
        if user_id in user_ids:
            logger.debug(f"Skipping duplicate user creation for ID: {user_id}")
            continue

        user = User(
            id=user_id,
            name=user_row.user_name,
            team=user_row.team_id,
        )
        User.replace(**user.__data__).execute()

        print(f"Created {user}")
        user_ids.add(user_id)
    return list(user_ids)


def _int_prompt(message: str, default: int, existing: int | None) -> int | None:
    raw = questionary.text(
        message,
        default=str(existing if existing is not None else default),
    ).ask()
    if raw is None or raw.strip() == "":
        return default if existing is None else existing
    try:
        return int(raw.strip())
    except ValueError:
        return default if existing is None else existing


def prompt_config(existing_config: Config | None) -> Config | None:
    challenge_name = questionary.text(
        "Enter a name for the challenge",
        default=existing_config.challenge_name if existing_config else "",
    ).ask()
    if not challenge_name:
        return None

    start_date = prompt_date(
        "Enter the start date of the challenge (in format YYYY-MM-DD, e.g. 2025-01-01)",
        existing_config.start_date if existing_config else None,
    )
    if not start_date:
        return None

    time_zone = questionary.select(
        "Select a time zone. Daily scores will be calculated based on this time zone.",
        choices=common_timezones,
        default=existing_config.time_zone if existing_config else "America/Los_Angeles",
    ).ask()
    if not time_zone:
        return None

    print("Scoring and tracking (press Enter for defaults):")
    max_daily = _int_prompt(
        "  Max active seconds per person per day (21600 = 6h, 0 = no cap)",
        21600,
        (
            getattr(existing_config, "max_daily_active_seconds", None)
            if existing_config
            else None
        ),
    )
    base_points = _int_prompt(
        "  Base points per hour",
        1,
        (
            getattr(existing_config, "base_points_per_hour", None)
            if existing_config
            else None
        ),
    )
    streak_bonus = _int_prompt(
        "  User streak bonus points (every N days)",
        5,
        (
            getattr(existing_config, "user_streak_bonus_points", None)
            if existing_config
            else None
        ),
    )
    streak_days = _int_prompt(
        "  User streak interval (days)",
        7,
        (
            getattr(existing_config, "user_streak_interval_days", None)
            if existing_config
            else None
        ),
    )
    team_bonus = _int_prompt(
        "  Team bonus points (when all active)",
        5,
        (
            getattr(existing_config, "team_bonus_points", None)
            if existing_config
            else None
        ),
    )
    strava_interval = _int_prompt(
        "  Strava request interval (seconds)",
        5,
        (
            getattr(existing_config, "strava_request_interval_seconds", None)
            if existing_config
            else None
        ),
    )

    kwargs = {
        "challenge_name": challenge_name,
        "start_date": start_date,
        "time_zone": time_zone,
        "max_daily_active_seconds": None if max_daily == 0 else max_daily,
        "base_points_per_hour": base_points,
        "user_streak_bonus_points": streak_bonus,
        "user_streak_interval_days": streak_days,
        "team_bonus_points": team_bonus,
        "strava_request_interval_seconds": strava_interval,
    }
    if existing_config:
        kwargs["point_thresholds"] = existing_config.point_thresholds
    return Config(**kwargs)


def initialize():
    create_tables()

    existing_config: Config | None = Config.select().first()
    config = prompt_config(existing_config)
    if not config:
        print("Config is incomplete, cancelling operation")
        return

    # Delete existing config entries so the config that is fetched is always the
    # latest one
    Config.delete().execute()
    config.save()
    logger.debug(f"Created {config}")

    print("Use the pop-up file explorer to select the user list for the challenge")
    user_list_path = prompt_select_file("user table", [FileType.csv])
    if not user_list_path:
        print("No file selected, cancelling operation")
        return

    try:
        user_list = parse_user_list(user_list_path)
    except Exception:
        logger.error(f"Failed to read user table:\n{traceback.format_exc()}")
        return

    team_ids = create_teams(user_list)
    user_ids = create_users(user_list)

    print(f"Created {len(team_ids)} team(s) and {len(user_ids)} user(s)")

    backup_db()
