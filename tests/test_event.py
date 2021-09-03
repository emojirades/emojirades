from unittest.mock import Mock, MagicMock

import pytest
import json

from emojirades.slack.event import Event, InvalidEvent
from .file_fixture import FileFixture


class TestEvent:
    mock_slack_client = Mock()
    mock_slack_client.bot_info = MagicMock(
        return_value={
            "id": "BOTID0001",
            "deleted": False,
            "name": "bot-tester",
            "updated": 1569646260,
            "app_id": "APPID0001",
            "user_id": "USERID007",
            "icons": {},
        }
    )

    @pytest.fixture
    def bot_event(self):
        with FileFixture("bot_event.json").open() as ff:
            return Event(json.load(ff), self.mock_slack_client)

    @pytest.fixture
    def user_event(self):
        with FileFixture("user_event.json").open() as ff:
            return Event(json.load(ff), self.mock_slack_client)

    @pytest.fixture
    def invalid_event(self):
        with FileFixture("invalid_event.json").open() as ff:
            return Event(json.load(ff), self.mock_slack_client)

    def test_get_user_player_id(self, user_event):
        assert user_event.player_id == "USERID002"

    def test_get_bot_player_id(self, bot_event):
        assert bot_event.player_id == "USERID007"

    def test_invalid_player_id(self, invalid_event):
        with pytest.raises(InvalidEvent):
            invalid_event.player_id

    def test_invalid_event(self, invalid_event):
        assert invalid_event.valid() is False

    def test_valid_event(self, bot_event, user_event):
        assert bot_event.valid() is True
        assert user_event.valid() is True
