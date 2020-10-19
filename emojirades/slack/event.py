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
        # Data shouldn't be empty
        if not self.data:
            return False

        # Events with a subtype are considered invalid
        # As they are all not related to a user 'guessing'
        allowed_subtypes = {
            "bot_message",
            "me_message",
        }

        if self.data.get("subtype") and not self.data["subtype"] in allowed_subtypes:
            return False

        # We assert each message event has a set of keys
        expected_keys = {
            "text",
            "channel",
        }

        if not expected_keys.issubset(self.data.keys()):
            return False

        # Player ID should be resolved correctly
        try:
            self.player_id
        except InvalidEvent:
            return False

        # If the event is coming from itself (the bot) ignore it
        if self.player_id == self.slack_client.bot_id:
            return False

        # Event is probably correct!
        return True
