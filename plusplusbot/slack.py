import time
from slackclient.server import SlackConnectionError, SlackLoginError
from slackclient import SlackClient as SC

import re

# TODO: this class needs to be fixed up


class SlackClient(object):
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.slack_client = SC(config)

        starterboth = self.slack_client.api_call("auth.test")
        self.bot_id = starterboth["user_id"]
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
        # We only want text based events
        if "text" not in event:
            return False

        # We ignore other bot messages
        if "bot_id" in event or ("user" in event and event["user"] == self.bot_id):
            return False

        # We only want events with a channel
        if "channel" not in event:
            return False

        event_channel_id = event["channel"]

        # Skip this event if the channel doesn't match and we're in a general channel
        if event_channel_id.startswith('C') and event_channel_id != self.channel_id:
            return False

        # We want time based text messages
        if "ts" not in event:
            return False

        # Maybe we read the same event twice off the firehose?
        event_timestamp = float(event.get("ts", "0"))
        if self.last_ts > event_timestamp:
            return False

        # Match on the bot reference being in the message
        bot_mention = "<@{0}>".format(self.bot_id)

        # The only direct message we listen to is one to us!
        if event_channel_id.startswith('D'):
            return True

        # Listen to group chats with a mention to us
        if event_channel_id.startswith('G') and bot_mention in event["text"]:
            return True

        # Listen to our registered channel chat for mentions
        if event_channel_id.startswith('C') and bot_mention in event["text"]:
            return True

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
                    #action(*args, **kwargs)
                else:
                    self.logger.debug("No Match: {0}".format(event))

            time.sleep(1)
