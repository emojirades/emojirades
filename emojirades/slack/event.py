import re
from emojirades.slack.slack_client import SlackClient


class InvalidEvent(Exception):
    pass


class Event:
    # pylint: disable=line-too-long
    user_override_regex = re.compile(
        r".*(?P<override_cmd>[\s]+player=[\s]*(<@(?P<user_override>[0-9A-Z]+)>)).*"
    )
    channel_override_regex = re.compile(
        r".*(?P<override_cmd>[\s]+channel=[\s]*(<#(?P<channel_override>[0-9A-Z]+)\|(?P<channel_name>[0-9A-Za-z_-]+)>)).*"
    )
    # pylint: enable=line-too-long

    def __init__(self, data, slack_client: SlackClient):
        self.data = data
        self.slack_client = slack_client

        self.original_channel = data.get("channel")
        self.original_player_id = None  # Resolved on first access to player_id

    @property
    def player_id(self):
        if self.original_player_id:
            return self.data.get("user", self.original_player_id)

        if "user" in self.data:
            self.original_player_id = self.data["user"]
        elif self.data.get("message", {}).get("user"):
            self.original_player_id = self.data["message"]["user"]
        elif "bot_id" in self.data:
            self.original_player_id = self.__get_bot_user_id()
        else:
            raise InvalidEvent("Can't find user id or bot id")

        return self.original_player_id

    @player_id.setter
    def player_id(self, value):
        if not self.original_player_id:
            # Trigger resolution of original_player_id
            _ = self.player_id
        self.data["user"] = value

    @property
    def text(self):
        return self.data["text"]

    @text.setter
    def text(self, value):
        self.data["text"] = value

    @property
    def channel(self):
        return self.data["channel"]

    @channel.setter
    def channel(self, value):
        self.data["channel"] = value

    def resolve_overrides(self, gamestate):
        """
        Resolves channel and player overrides if the original user is an admin
        """
        original_user = self.player_id
        original_channel = self.channel

        # Perform the channel override if it matches
        channel_override_match = self.channel_override_regex.match(self.text)

        if channel_override_match:
            new_channel = channel_override_match.groupdict()["channel_override"]

            if (
                isinstance(new_channel, str)
                and new_channel[0] in ("G", "C")
                and gamestate.is_admin(new_channel, original_user)
            ):
                self.channel = new_channel
                self.text = self.text.replace(
                    channel_override_match.groupdict()["override_cmd"], ""
                )

        # Only check for user override if the user is an admin in the (potentially overridden) channel
        if self.is_game_channel and gamestate.is_admin(self.channel, original_user):
            user_override_match = self.user_override_regex.match(self.text)

            if user_override_match:
                self.player_id = user_override_match.groupdict()["user_override"]
                self.text = self.text.replace(
                    user_override_match.groupdict()["override_cmd"], ""
                )

    @property
    def is_game_channel(self):
        """Game channels are non-DM channels"""
        return isinstance(self.data["channel"], str) and self.data["channel"][0] in (
            "G",
            "C",
        )

    # pylint: disable=invalid-name
    @property
    def ts(self):
        return self.data["ts"]

    # pylint: enable=invalid-name

    @property
    def is_edit(self):
        return self.data.get("subtype", "") == "message_changed"

    @property
    def is_recent_edit(self):
        """Recent is defined as 30 seconds"""
        if not self.is_edit:
            return False

        current_ts = float(self.ts)
        previous_ts = float(self.data["previous_message"]["ts"])

        if (current_ts - previous_ts) <= 30:
            return True

        return False

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
            "message_changed",
        }

        if self.data.get("subtype"):
            if not self.data["subtype"] in allowed_subtypes:
                return False

            if self.data["subtype"] == "message_changed":
                self.data["text"] = self.data["message"]["text"]

        # We assert each message event has a set of keys
        expected_keys = {
            "text",
            "channel",
            "ts",
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
