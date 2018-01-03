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

        slack_bot_token = os.environ.get("SLACK_BOT_TOKEN", None)

        if slack_bot_token is not None:
            self.slack = SlackClient(os.environ.get('SLACK_BOT_TOKEN'), self.logger)
        else:
            raise RuntimeError("Missing SLACK_BOT_TOKEN from environment vars")

        self.logger.debug("Initialised application instance")

    def match_event(self, event, commands):
        """
        If the event is valid and matches a command, perform the action the command details
        :param event:
        :return:
        """

        self.logger.debug("Handling event: {}".format(event))

        if "text" not in event:
            return None

        for pattern, (Command, description) in commands.items():
            if Command.match(event["text"], me=self.slack.bot_id):
                return Command(self.scorekeeper, self.slack, event)

        return None

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
                    self.logger.debug("Matched {0} for event {1}".format(action, event))
                    response = action.execute()

                    if response:
                        self.slack.sc.rtm_send_message(event["channel"], response)

                else:
                    self.logger.debug("No match for event {0}".format(event))

            time.sleep(1)
