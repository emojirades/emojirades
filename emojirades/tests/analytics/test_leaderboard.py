from emojirades.analytics.leaderboard import LeaderBoard

import pendulum
import pytest
import json

from emojirades.tests.FileFixture import FileFixture


class TestLeaderBoard:
    @pytest.fixture
    def lb(self):
        with FileFixture("history.json").open() as ff:
            return LeaderBoard(json.load(ff))

    @pytest.fixture
    def current_date(self, mel_tz):
        return pendulum.datetime(2020, 6, 20, tz=mel_tz)

    @pytest.fixture
    def mel_tz(self):
        return pendulum.timezone("Australia/Melbourne")

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

    def test_get_historical_month(self, lb, mel_tz):

        historical_date = pendulum.datetime(2020, 5, 10, tz=mel_tz)

        assert lb.get_month(historical_date) == [
            ("U5HKU1Q0W", 74),
            ("U0ZC11HC7", 64),
            ("U0VCW825A", 57),
            ("U985L6R1M", 41),
        ]
