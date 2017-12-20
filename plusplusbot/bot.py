import os

import time

from plusplusbot.slack import SlackClient
from plusplusbot.scorekeeper import ScoreKeeper

from plusplusbot.commands import Command

import logging

module_logger = logging.getLogger("PlusPlusBot.bot")


class PlusPlusBot(object):
    def __init__(self, score_file=None):
        self.logger = logging.getLogger("PlusPlusBot.bot.Bot")

        self.scorekeeper = ScoreKeeper(score_file)
        self.slack = SlackClient(os.environ.get('SLACK_BOT_TOKEN'), self.logger)
        self.logger.debug("Initialised application instance")

    def match_event(self, event, actions):
        """
        If the event is directed at the bot, return true, else false
        :param event:
        :return:
        """

        self.logger.debug("Handling event: {}".format(event))

        for pattern, command in actions.items():
            if "text" in event and command[0].match(event["text"], me=self.slack.bot_id):
                return actions[pattern][0](self.scorekeeper, self.slack, event)
        return False

    def listen_for_actions(self):
        actions = Command.prepare_commands()

        if not self.slack.ready:
            raise RuntimeError("is_ready has not been called/returned false")

        if not self.slack.sc.rtm_connect():
            raise RuntimeError("Failed to connect to the Slack API")

        self.logger.info("Slack is connected and listening for actions")

        while True:
            for event in self.slack.sc.rtm_read():
                if not event:
                    continue

                # action, args, kwargs = self.match_event(event, actions)
                action = self.match_event(event, actions)

                if action:
                    self.logger.debug("Matched: {0}".format(event))
                    response = action.execute()

                    if response:
                        self.slack.sc.rtm_send_message(event["channel"], response)

                else:
                    self.logger.debug("No Match: {0}".format(event))

            time.sleep(1)
