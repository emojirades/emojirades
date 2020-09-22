import math
from unittest import TestCase

from emojirades.analytics.time_range import TimeRange
import pendulum


class TestTimeRange(TestCase):
    def test_get_start_date_of_week(self):
        start_date = TimeRange.get_start_date(
            pendulum.DateTime(2020, 9, 16), TimeRange.WEEKLY
        )

        assert start_date == pendulum.DateTime(2020, 9, 14)

    def test_get_start_date_of_month(self):
        start_date = TimeRange.get_start_date(
            pendulum.DateTime(2020, 9, 16), TimeRange.MONTHLY
        )

        assert start_date == pendulum.DateTime(2020, 9, 1)

    def test_get_end_date_of_week(self):
        end_date = TimeRange.get_end_date(
            pendulum.DateTime(2020, 9, 16), TimeRange.WEEKLY
        )

        assert end_date == pendulum.DateTime(2020, 9, 20, 23, 59, 59, 999999)

    def test_get_end_date_of_month(self):
        end_date = TimeRange.get_end_date(
            pendulum.DateTime(2020, 9, 16), TimeRange.MONTHLY
        )

        assert end_date == pendulum.DateTime(2020, 9, 30, 23, 59, 59, 999999)
