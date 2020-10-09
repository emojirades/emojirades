from emojirades.slack.slack_client import SlackClient


class InvalidEvent(Exception):
    pass


class Event:
    def __init__(self, data, slack_client: SlackClient):
        self.data = data
        self.slack_client = slack_client

    @property
    def player_id(self):
        if "user" in self.data:
            return self.data["user"]
        elif "bot_id" in self.data:
            return self.__get_bot_user_id()
        else:
            raise InvalidEvent("Can't find user id or bot id")

    @property
    def text(self):
        return self.data["text"]

    @text.setter
    def text(self, value):
        self.data["text"] = value

    @property
    def channel(self):
        return self.data["channel"]

    @property
    def ts(self):
        return self.data["ts"]

    def __get_bot_user_id(self):
        return self.slack_client.bot_info(self.data["bot_id"])["user_id"]

    def valid(self) -> bool:
        """
        Assert the lowest level of things we need to see in an event to be parseable
        :return bool:
        """
        expected_keys = {
            "text",
            "channel",
        }

        if not self.data:
            return False
        elif not expected_keys.issubset(self.data.keys()):
            return False
        else:
            try:
                self.player_id
            except InvalidEvent:
                return False

            # If the event is coming from itself (the bot) ignore it
            if self.player_id == self.slack_client.bot_id:
                return False

        return True
