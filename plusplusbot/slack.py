import time
from slackclient.server import SlackConnectionError, SlackLoginError
from slackclient import SlackClient as SC

import re

# TODO: this class needs to be fixed up


class SlackClient(object):
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.sc = SC(config)

        epp_bot = self.sc.api_call("auth.test")
        self.bot_id = epp_bot["user_id"]
        # self.channel_id = config.get("channel_id", None)
        # self.channel_id = None

        self.ready = True
        self.last_ts = float(0)
