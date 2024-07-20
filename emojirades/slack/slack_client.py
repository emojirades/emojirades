import logging

from expiringdict import ExpiringDict

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from emojirades.persistence import get_auth_handler


class SlackClient:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, auth_uri, extra_slack_kwargs=None, existing_client=None):
        self.logger = logging.getLogger("EmojiradesBot.slack.SlackClient")

        self.existing_client = None
        self.app = None
        self.handler = None

        if auth_uri is None and existing_client is not None:
            self.existing_client = existing_client
        else:
            self.config = get_auth_handler(auth_uri).load()

            if extra_slack_kwargs is None:
                extra_slack_kwargs = {}

            self.app = App(token=self.config["bot_access_token"])
            self.handler = SocketModeHandler(self.app, self.config["slack_app_token"])

        self.last_ts = float(0)

        self.user_info_cache = ExpiringDict(
            max_len=100, max_age_seconds=172800
        )  # 2 days
        self.bot_user_info_cache = ExpiringDict(
            max_len=100, max_age_seconds=172800
        )  # 2 days

        response = self.client.auth_test()

        self.bot_id = response["user_id"]
        self.workspace_id = response["team_id"]
        self.handler.workspace_id = response["team_id"]

        self.bot_name = self.user_info(self.bot_id)["real_name"]

    @property
    def client(self):
        if self.existing_client is not None:
            return self.existing_client

        return self.app.client

    def start(self, blocking=True):
        if blocking:
            self.handler.start()
        else:
            self.handler.connect()

    def user_info(self, user_id):
        user = self.user_info_cache.get(user_id)

        if user is None:
            user = self.client.users_info(user=user_id)["user"]
            self.user_info_cache[user_id] = user

        return user

    def bot_info(self, bot_id):
        bot_user = self.bot_user_info_cache.get(bot_id)

        if not bot_user:
            bot_user = self.client.bots_info(bot=bot_id)["bot"]
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
        response = self.client.conversations_open(users=[user_id])

        if response["ok"]:
            return response["channel"]["id"]

        return None
