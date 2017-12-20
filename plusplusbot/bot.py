import os

import time

from plusplusbot.slack import SlackClient
from plusplusbot.scorekeeper import ScoreKeeper

from plusplusbot.commands import *

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
        actions = self.prepare_commands()

        if not self.slack.ready:
            raise RuntimeError("is_ready has not been called/returned false")

        if not self.slack.sc.rtm_connect():
            raise RuntimeError("Failed to connect to the Slack API")

        self.logger.info("Slack is connected and listening for actions")
        #help_message = self.build_help_message(actions)

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

    def prepare_commands(self):
        commands = [
            PlusPlusCommand,
            MinusMinusCommand,
            LeaderboardCommand,
            SetCommand
        ]

        return {command.pattern: (command, command.description) for command in commands}

    def build_help_message(self):
        message = "Available commands are:\n```"
        message += "{0:<20}{1}\n".format("Command", "Help")

        for action in self.actions:
            message += "{0:<20}{1}\n".format(action[0], action[1])

        return message