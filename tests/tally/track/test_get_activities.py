from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from tally.actions.track.activity import get_activities
from tally.models.validation.club_feed import ActivityStatsEntry
from tally.services.strava import StravaService
from tests.tally.mocks.mock_team import create_team
from tests.tally.mocks.mock_user import create_user
from tests.tally.mocks.mock_club_feed import (
    create_feed_response,
    create_feed_response_pagination,
    create_athlete,
    create_feed_activity,
    create_feed_entry_single_activity,
    create_feed_entry_multiple_activities,
    create_row_data,
    create_cursor_data,
)


class TestGetActivities:
    @patch("tally.actions.track.activity.time.sleep")
    def test_filter_out_activities_not_by_user_in_team(self, mock_sleep, mock_db):
        # Create a team with one user in the database
        team = create_team(id="team1", name="Test Team")
        team.save(force_insert=True)
        create_user(id="user1", name="Team Member", team=team.id).save(
            force_insert=True
        )

        # Create a mock Strava service
        mock_strava_service = MagicMock(spec=StravaService)

        # Create a mock club feed with an activity from a user NOT in the team
        user_not_in_team = create_athlete(
            athlete_id="user_not_in_team", athlete_name="Outsider"
        )
        activity_from_outsider = create_feed_activity(
            id="activity123",
            athlete=user_not_in_team,
            activity_name="Outsider's Run",
            activity_type="Run",
        )

        mock_feed = create_feed_response(
            entries=[create_feed_entry_single_activity(activity=activity_from_outsider)]
        )

        # Mock the get_club_feed method to return our mock feed
        mock_strava_service.get_club_feed.return_value = mock_feed

        # Call get_activities
        after_date = datetime.now(timezone.utc)
        result_activities = get_activities(mock_strava_service, team, after_date)

        # Assert that the activity from the user not in the team is filtered out
        assert len(result_activities) == 0

        # Verify that get_club_feed was called with the correct team id
        mock_strava_service.get_club_feed.assert_called_once_with("team1", None)

    @patch("tally.actions.track.activity.time.sleep")
    def test_include_activities_from_users_in_team(self, mock_sleep, mock_db):
        # Create a team with one user in the database
        team = create_team(id="team1", name="Test Team")
        team.save(force_insert=True)
        create_user(id="user1", name="Team Member", team=team.id).save(
            force_insert=True
        )

        # Create a mock Strava service
        mock_strava_service = MagicMock(spec=StravaService)

        # Create a mock club feed with an activity from a user IN the team
        user_in_team = create_athlete(athlete_id="user1", athlete_name="Team Member")
        moving_time_stats = [
            ActivityStatsEntry(
                key="moving_time",
                value="30<abbr class='unit' title='minute'>m</abbr> 0<abbr class='unit' title='second'>s</abbr>",
            )
        ]
        activity_from_team_member = create_feed_activity(
            id="activity456",
            athlete=user_in_team,
            activity_name="Team Member's Run",
            activity_type="Run",
            elapsed_time=3600,
            start_date="2024-01-15T10:00:00Z",
            stats=moving_time_stats,
        )

        mock_feed = create_feed_response(
            entries=[
                create_feed_entry_single_activity(activity=activity_from_team_member)
            ]
        )

        # Mock the get_club_feed method to return our mock feed
        mock_strava_service.get_club_feed.return_value = mock_feed

        # Call get_activities
        after_date = datetime.now(timezone.utc)
        result_activities = get_activities(mock_strava_service, team, after_date)

        # Assert that the activity from the team member is included
        assert len(result_activities) == 1

        # Verify the activity details including start_time and moving_seconds
        activity = result_activities[0]
        assert activity.id == "activity456"
        assert activity.user.id == "user1"
        assert activity.title == "Team Member's Run"
        assert activity.workout_type == "Run"
        assert activity.elapsed_seconds == 3600
        assert activity.moving_seconds == 30 * 60  # 30 minutes
        # start_time is set by map_feed_activity_to_activity as datetime from ISO string
        assert activity.start_time == datetime.fromisoformat(
            "2024-01-15T10:00:00+00:00"
        )

        # Verify that get_club_feed was called with the correct team id
        mock_strava_service.get_club_feed.assert_called_once_with("team1", None)

    @patch("tally.actions.track.activity.time.sleep")
    def test_empty_feed_returns_empty_list(self, mock_sleep, mock_db):
        """Test that an empty feed response returns no activities"""
        team = create_team(id="team1", name="Test Team")
        team.save(force_insert=True)
        create_user(id="user1", name="Team Member", team=team.id).save(
            force_insert=True
        )

        mock_strava_service = MagicMock(spec=StravaService)
        mock_feed = create_feed_response(
            entries=[],
            pagination=create_feed_response_pagination(has_more=False),
        )
        mock_strava_service.get_club_feed.return_value = mock_feed

        after_date = datetime.now(timezone.utc)
        result_activities = get_activities(mock_strava_service, team, after_date)

        assert len(result_activities) == 0
        mock_strava_service.get_club_feed.assert_called_once_with("team1", None)

    @patch("tally.actions.track.activity.time.sleep")
    def test_feed_entry_multiple_activities_included(self, mock_sleep, mock_db):
        """Test that activities from FeedEntryMultipleActivities (variant B) are included"""
        team = create_team(id="team1", name="Test Team")
        team.save(force_insert=True)
        create_user(id="user1", name="Team Member", team=team.id).save(
            force_insert=True
        )

        mock_strava_service = MagicMock(spec=StravaService)
        user_in_team = create_athlete(athlete_id="user1", athlete_name="Team Member")
        activity1 = create_feed_activity(
            id="multi_act_1",
            athlete=user_in_team,
            activity_name="First Activity",
            activity_type="Run",
            start_date="2024-01-14T09:00:00Z",
            elapsed_time=1800,
        )
        activity2 = create_feed_activity(
            id="multi_act_2",
            athlete=user_in_team,
            activity_name="Second Activity",
            activity_type="Ride",
            start_date="2024-01-14T14:00:00Z",
            elapsed_time=3600,
        )
        row_data = create_row_data(activities=[activity1, activity2])
        multi_entry = create_feed_entry_multiple_activities(row_data=row_data)
        mock_feed = create_feed_response(
            entries=[multi_entry],
            pagination=create_feed_response_pagination(has_more=False),
        )
        mock_strava_service.get_club_feed.return_value = mock_feed

        after_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result_activities = get_activities(mock_strava_service, team, after_date)

        assert len(result_activities) == 2
        ids = {a.id for a in result_activities}
        assert ids == {"multi_act_1", "multi_act_2"}
        mock_strava_service.get_club_feed.assert_called_once_with("team1", None)

    @patch("tally.actions.track.activity.time.sleep")
    def test_pagination_fetches_multiple_pages(self, mock_sleep, mock_db):
        """Test that get_activities pages when hasMore is True and stops when hasMore is False"""
        team = create_team(id="team1", name="Test Team")
        team.save(force_insert=True)
        create_user(id="user1", name="Team Member", team=team.id).save(
            force_insert=True
        )

        mock_strava_service = MagicMock(spec=StravaService)
        user_in_team = create_athlete(athlete_id="user1", athlete_name="Team Member")
        after_ts = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
        # Page 1: one activity, hasMore True, cursor from updated_at
        cursor_page1 = int(after_ts) + 1000
        activity_page1 = create_feed_activity(
            id="page1_activity",
            athlete=user_in_team,
            activity_name="Page 1",
            activity_type="Run",
            start_date="2024-01-15T10:00:00Z",
            elapsed_time=3600,
        )
        feed_page1 = create_feed_response(
            entries=[
                create_feed_entry_single_activity(
                    cursor_data=create_cursor_data(updated_at=cursor_page1),
                    activity=activity_page1,
                )
            ],
            pagination=create_feed_response_pagination(has_more=True),
        )
        # Page 2: one activity, hasMore False
        activity_page2 = create_feed_activity(
            id="page2_activity",
            athlete=user_in_team,
            activity_name="Page 2",
            activity_type="Run",
            start_date="2024-01-16T10:00:00Z",
            elapsed_time=1800,
        )
        feed_page2 = create_feed_response(
            entries=[create_feed_entry_single_activity(activity=activity_page2)],
            pagination=create_feed_response_pagination(has_more=False),
        )
        mock_strava_service.get_club_feed.side_effect = [feed_page1, feed_page2]

        after_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result_activities = get_activities(mock_strava_service, team, after_date)

        assert len(result_activities) == 2
        assert mock_strava_service.get_club_feed.call_count == 2
        mock_strava_service.get_club_feed.assert_any_call("team1", None)
        mock_strava_service.get_club_feed.assert_any_call("team1", cursor_page1)
