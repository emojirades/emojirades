import os

from plusplusbot.slack import SlackClient
from plusplusbot.scorekeeper import ScoreKeeper

from plusplusbot.commands import *

import logging

module_logger = logging.getLogger("PlusPlusBot.bot")


class PlusPlusBot(object):
    def __init__(self, score_file=None):
        self.logger = logging.getLogger("PlusPlusBot.bot.Bot")

        self.scorekeeper = ScoreKeeper(score_file)
        self.slack = SlackClient(os.environ.get('SLACK_BOT_TOKEN'), self.scorekeeper, self.logger)
        self.logger.debug("Initialised application instance")

    def listen(self):
        self.slack.listen_for_actions(self.prepare_commands())

    def prepare_commands(self):
        commands = [
            PlusPlusCommand,
            MinusMinusCommand
        ]

        return {command.pattern: (command, command.description) for command in commands}

