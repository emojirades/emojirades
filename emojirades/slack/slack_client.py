import logging

from expiringdict import ExpiringDict

import slack_sdk

from emojirades.persistence import get_auth_handler


class SlackClient:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, auth_uri, extra_slack_kwargs=None, existing_client=None):
        self.logger = logging.getLogger("EmojiradesBot.slack.SlackClient")

        if auth_uri is None and existing_client is not None:
            self.rtm = existing_client
        else:
            self.config = get_auth_handler(auth_uri).load()

            if extra_slack_kwargs is None:
                extra_slack_kwargs = {}

            # pylint: disable=no-member
            self.rtm = slack_sdk.rtm_v2.RTMClient(
                token=self.config["bot_access_token"],
                logger=self.logger,
                **extra_slack_kwargs,
            )
            # pylint: enable=no-member

        self.last_ts = float(0)

        self.user_info_cache = ExpiringDict(
            max_len=100, max_age_seconds=172800
        )  # 2 days
        self.bot_user_info_cache = ExpiringDict(
            max_len=100, max_age_seconds=172800
        )  # 2 days

        response = self.rtm.web_client.auth_test()

        self.bot_id = response["user_id"]
        self.workspace_id = response["team_id"]
        self.rtm.workspace_id = response["team_id"]

        self.bot_name = self.user_info(self.bot_id)["real_name"]

    def start(self, blocking=True):
        if blocking:
            self.rtm.start()
        else:
            self.rtm.connect()

    def user_info(self, user_id):
        user = self.user_info_cache.get(user_id)

        if user is None:
            user = self.rtm.web_client.users_info(user=user_id)["user"]
            self.user_info_cache[user_id] = user

        return user

    def bot_info(self, bot_id):
        bot_user = self.bot_user_info_cache.get(bot_id)

        if not bot_user:
            bot_user = self.rtm.web_client.bots_info(bot=bot_id)["bot"]
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
        response = self.rtm.web_client.conversations_open(users=[user_id])

        if response["ok"]:
            return response["channel"]["id"]

        return None
