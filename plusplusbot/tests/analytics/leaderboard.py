from plusplusbot.analytics.leaderboard import LeaderBoard
import pytest
import json


class TestLeaderBoard:

    @pytest.fixture
    def lb(self):
        history = json.load(open("../fixtures/history.json"))
        return LeaderBoard(history)

    def test_fixture_loading(self, lb):
        assert len(lb.history) > 0

    def test_get_week(self):
        lb = LeaderBoard([])

        assert lb.get_week() == 100
