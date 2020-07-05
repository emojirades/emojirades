import pendulum

from plusplusbot.analytics.leaderboard import LeaderBoard
import pytest
import json


class TestLeaderBoard:
    @pytest.fixture
    def lb(self):
        history = json.load(open("../fixtures/history.json"))
        return LeaderBoard(history)

    @pytest.fixture
    def current_date(self):
        return pendulum.datetime(
            2020, 6, 20, tz=pendulum.timezone("Australia/Melbourne")
        )

    def test_fixture_loading(self, lb):
        assert len(lb.history) > 0

    def test_get_week(self, lb, current_date):
        assert lb.get_week(current_date) == [
            ("U985L6R1M", 15),
            ("U0VCW825A", 13),
            ("U5HKU1Q0W", 12),
            ("U0ZC11HC7", 9),
        ]

    def test_get_month(self, lb, current_date):
        assert lb.get_month(current_date) == [
            ("U0VCW825A", 44),
            ("U5HKU1Q0W", 43),
            ("U985L6R1M", 42),
            ("U0ZC11HC7", 33),
        ]
