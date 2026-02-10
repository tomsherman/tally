import pytest

from tally.actions.score.point_system import calculate_user_points


class TestCalculateUserPoints:
    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0, 0),
            (1, 0),
            (59, 0),
            (60, 0),
            (5 * 60, 0),
            (15 * 60, 0),
            (29 * 60 + 59, 0),
            (30 * 60, 5),
            (30 * 60 + 1, 5),
            (45 * 60, 5),
            (59 * 60 + 59, 5),
            (60 * 60, 8),
            (60 * 60 + 1, 8),
            (90 * 60, 8),
            (119 * 60 + 59, 8),
            (120 * 60, 10),
            (120 * 60 + 1, 10),
            (150 * 60, 10),
            (174 * 60, 10),
            (180 * 60, 11),
            (240 * 60, 12),
            (1 * 3600, 8),
            (2 * 3600, 10),
            (3 * 3600, 11),
            (4 * 3600, 12),
            (5 * 3600, 13),
            (10 * 3600, 18),
            (24 * 3600, 32),
        ],
    )
    def test_calculate_user_points(self, seconds, expected):
        """Test point calculation for various active durations."""
        assert calculate_user_points(seconds) == expected

    def test_return_type_is_int(self):
        """Test that the function returns an int"""
        result = calculate_user_points(1800)  # 30 minutes
        assert isinstance(result, int)
        assert result == 5
