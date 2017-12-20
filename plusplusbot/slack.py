import time
from slackclient.server import SlackConnectionError, SlackLoginError
from slackclient import SlackClient as SC

import re

# TODO: this class needs to be fixed up


class SlackClient(object):
    def __init__(self, config, scorekeeper, logger):
        self.config = config
        self.scorekeeper = scorekeeper
        self.logger = logger
        self.slack_client = SC(config)

        epp_bot = self.slack_client.api_call("auth.test")
        self.bot_id = epp_bot["user_id"]
        # self.channel_id = config.get("channel_id", None)
        self.channel_id = None

        self.ready = True
        self.last_ts = float(0)

    @staticmethod
    def build_help_message(actions):
        message = "Available commands are:\n```"
        message += "{0:<20}{1}\n".format("Command", "Help")

        for action in actions:
            message += "{0:<20}{1}\n".format(action[0], action[1])

        return message

    def match_event(self, event, actions):
        """
        If the event is directed at the bot, return true, else false
        :param event: 
        :return: 
        """

        self.logger.debug("Handling event: {}".format(event))

        for pattern in actions.keys():
            if "text" in event and re.match(pattern, event["text"]):
                return actions[pattern][0](self.scorekeeper, event)
        return False

    def listen_for_actions(self, actions):
        if not self.ready:
            raise RuntimeError("is_ready has not been called/returned false")

        if not self.slack_client.rtm_connect():
            raise RuntimeError("Failed to connect to the Slack API")

        self.logger.info("Slack is connected and listening for actions")
        help_message = self.build_help_message(actions)

        while True:
            for event in self.slack_client.rtm_read():
                if not event:
                    continue

                # action, args, kwargs = self.match_event(event, actions)
                action = self.match_event(event, actions)

                if action:
                    self.logger.debug("Matched: {0}".format(event))
                    response = action.execute()

                    if response:
                        self.slack_client.rtm_send_message(event["channel"], response)

                else:
                    self.logger.debug("No Match: {0}".format(event))

            time.sleep(1)
