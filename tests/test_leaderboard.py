import datetime

from zoneinfo import ZoneInfo

from emojirades.analytics.scoreboard import ScoreboardAnalytics

import pytest
import json

from emojirades.analytics.time_unit import TimeUnit
from .file_fixture import FileFixture


class TestScoreboardAnalytics:
    @pytest.fixture
    def lb(self, mel_tz):
        with FileFixture("history.json").open() as ff:
            history = json.load(ff)

        for item in history:
            item["timestamp"] = datetime.datetime.strptime(
                item["timestamp"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=mel_tz)

        return ScoreboardAnalytics(history)

    @pytest.fixture
    def current_date(self, mel_tz):
        return datetime.datetime(2020, 6, 20, tzinfo=mel_tz)

    @pytest.fixture
    def mel_tz(self):
        return ZoneInfo("Australia/Melbourne")

    def test_fixture_loading(self, lb):
        assert len(lb.history) > 0

    def test_get_week(self, lb, current_date):
        assert lb.get(current_date, TimeUnit.WEEKLY) == [
            ("U985L6R1M", 15),
            ("U0VCW825A", 13),
            ("U5HKU1Q0W", 12),
            ("U0ZC11HC7", 9),
        ]

    def test_get_month(self, lb, current_date):
        assert lb.get(current_date, TimeUnit.MONTHLY) == [
            ("U0VCW825A", 44),
            ("U5HKU1Q0W", 43),
            ("U985L6R1M", 42),
            ("U0ZC11HC7", 33),
        ]

    def test_get_historical_month(self, lb, mel_tz):
        historical_date = datetime.datetime(2020, 5, 10, tzinfo=mel_tz)

        assert lb.get(historical_date, TimeUnit.MONTHLY) == [
            ("U5HKU1Q0W", 74),
            ("U0ZC11HC7", 64),
            ("U0VCW825A", 57),
            ("U985L6R1M", 41),
        ]
