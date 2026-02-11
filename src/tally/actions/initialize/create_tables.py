import logging

from tally.services.db import db
from tally.models.db import ALL_MODELS


logger = logging.getLogger(__name__)


def _migrate_config_if_needed():
    """Add new scoring/tracking columns to existing Config table if missing."""
    cursor = db.execute_sql("PRAGMA table_info(config)")
    existing = {row[1] for row in cursor.fetchall()}
    cursor.close()

    columns_to_add = [
        ("max_daily_active_seconds", "INTEGER DEFAULT 21600"),
        ("base_points_per_hour", "INTEGER DEFAULT 1"),
        (
            "point_thresholds",
            'TEXT DEFAULT \'[{"minutes": 30, "points": 5}, {"minutes": 60, "points": 2}, {"minutes": 120, "points": 1}]\'',
        ),
        ("user_streak_bonus_points", "INTEGER DEFAULT 5"),
        ("user_streak_interval_days", "INTEGER DEFAULT 7"),
        ("team_bonus_points", "INTEGER DEFAULT 5"),
        ("strava_request_interval_seconds", "INTEGER DEFAULT 5"),
    ]
    for name, spec in columns_to_add:
        if name not in existing:
            logger.debug("Adding column config.%s", name)
            db.execute_sql(f"ALTER TABLE config ADD COLUMN {name} {spec}")


def create_tables():
    logger.debug("Creating tables if they do not exist: %s", ALL_MODELS)
    db.create_tables(ALL_MODELS, safe=True)
    _migrate_config_if_needed()
