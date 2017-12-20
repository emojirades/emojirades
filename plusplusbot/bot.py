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
        self.slack.listen_for_actions({
            PlusPlusCommand.pattern: (PlusPlusCommand, "Increment the users score"),
            "<@[0-9A-Z].*> --": (self.scorekeeper.minusminus, "Decrement the users score"),
            "<@[0-9A-Z].*> set [0-9]+": (self.scorekeeper.overwrite, "Manually set the users score"),
            "@{me} leaderboard": (self.scorekeeper.leaderboard, "Shows all the users scores"),
            "@{me} history": (self.scorekeeper.history, "Shows the last few actions"),
            "@{me} export": (self.scorekeeper.export, "Export leader∂board in CSV"),
        })
