import json
import logging
import threading

from expiringdict import ExpiringDict
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient

from emojirades.persistence import get_auth_repository


class SlackClient:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, auth_uri, extra_slack_kwargs=None):
        self.logger = logging.getLogger("EmojiradesBot.slack.SlackClient")

        self.config = get_auth_repository(auth_uri).load()

        if extra_slack_kwargs is None:
            extra_slack_kwargs = {}

        web_kwargs = {}
        socket_mode_kwargs = {}

        if "base_url" in extra_slack_kwargs:
            web_kwargs["base_url"] = extra_slack_kwargs["base_url"]

        for key in (
            "auto_reconnect_enabled",
            "trace_enabled",
            "all_message_trace_enabled",
            "ping_pong_trace_enabled",
            "ping_interval",
        ):
            if key in extra_slack_kwargs:
                socket_mode_kwargs[key] = extra_slack_kwargs[key]

        bot_token = self.config.get("bot_access_token")
        app_token = self.config.get("app_token", self.config.get("bot_app_token", "xapp-default"))

        self.web_client = WebClient(
            token=bot_token,
            logger=self.logger,
            **web_kwargs,
        )

        self.socket_mode = SocketModeClient(
            app_token=app_token,
            web_client=self.web_client,
            logger=self.logger,
            **socket_mode_kwargs,
        )

        self.last_ts = float(0)
        self.cache_lock = threading.Lock()

        self.user_info_cache = ExpiringDict(max_len=100, max_age_seconds=172800)  # 2 days
        self.bot_user_info_cache = ExpiringDict(max_len=100, max_age_seconds=172800)  # 2 days

        response = self.web_client.auth_test()

        self.bot_id = response["user_id"]
        self.workspace_id = response["team_id"]
        self.socket_mode.workspace_id = response["team_id"]

        self.bot_name = self.user_info(self.bot_id)["real_name"]

    def start(self, blocking=True):
        self.socket_mode.connect()

    def close(self):
        self.socket_mode.close()

    def send_event(self, event: dict):
        req_dict = {
            "type": "events_api",
            "envelope_id": "test-envelope-id",
            "payload": {
                "event": event,
            },
        }
        self.socket_mode.run_message_listeners(req_dict, json.dumps(req_dict))

    def user_info(self, user_id):
        with self.cache_lock:
            user = self.user_info_cache.get(user_id)

        if user is None:
            user = self.web_client.users_info(user=user_id)["user"]
            with self.cache_lock:
                self.user_info_cache[user_id] = user

        return user

    def bot_info(self, bot_id):
        with self.cache_lock:
            bot_user = self.bot_user_info_cache.get(bot_id)

        if not bot_user:
            bot_user = self.web_client.bots_info(bot=bot_id)["bot"]
            with self.cache_lock:
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
        response = self.web_client.conversations_open(users=[user_id])

        if response["ok"]:
            return response["channel"]["id"]

        return None
