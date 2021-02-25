from emojirades.handlers import get_configuration_handler
from expiringdict import ExpiringDict

import slack
import json


def get_handler(filename):
    class SlackAuthConfigHandler(get_configuration_handler(filename)):
        """
        Handles CRUD of the Slack Auth configuration file
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def load(self):
            bytes_content = super().load()

            if bytes_content is None or not bytes_content:
                return None

            return json.loads(bytes_content.decode("utf-8"))

        def save(self, state):
            raise RuntimeError("Saving SlackAuth file not implemented")

    return SlackAuthConfigHandler(filename)


class SlackClient(object):
    def __init__(self, filename, logger=None):
        self.config = get_handler(filename).load()
        self.logger = logger

        self.rtmclient = slack.RTMClient(token=self.config["bot_access_token"])
        self.webclient = slack.WebClient(
            token=self.config["bot_access_token"], timeout=30
        )

        self.last_ts = float(0)

        self.user_info_cache = ExpiringDict(
            max_len=100, max_age_seconds=172800
        )  # 2 days
        self.bot_user_info_cache = ExpiringDict(
            max_len=100, max_age_seconds=172800
        )  # 2 days

        self.bot_id = self.webclient.auth_test()["user_id"]
        self.bot_name = self.user_info(self.bot_id)["real_name"]

    def start(self):
        self.rtmclient.start()

    def set_webclient(self, webclient):
        self.webclient = webclient

    def user_info(self, user_id):
        user = self.user_info_cache.get(user_id)

        if user is None:
            user = self.webclient.users_info(user=user_id)["user"]
            self.user_info_cache[user_id] = user

        return user

    def bot_info(self, bot_id):
        bot_user = self.bot_user_info_cache.get(bot_id)

        if not bot_user:
            bot_user = self.webclient.bots_info(bot=bot_id)["bot"]
            self.bot_user_info_cache[bot_id] = bot_user

        return bot_user

    def is_bot(self, user_id):
        return self.user_info(user_id)["is_bot"] or user_id == "USLACKBOT"

    def is_admin(self, user_id):
        return self.user_info(user_id)["is_admin"]

    def get_names(self, user_id):
        user = self.user_info(user_id)

        return {
            "name": user["name"],
            "real_name": user["real_name"],
        }

    def pretty_name(self, user_id):
        user = self.user_info(user_id)
        return user.get("real_name", user.get("name", "Unknown User"))

    def find_im(self, user_id):
        # Open or resume a direct message with the target user
        response = self.webclient.conversations_open(users=[user_id])

        if response["ok"]:
            return response["channel"]["id"]

        return None
