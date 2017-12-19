import os

from plusplusbot.slack import SlackClient
from plusplusbot.scorekeeper import ScoreKeeper

import logging

module_logger = logging.getLogger("PlusPlusBot.bot")


class PlusPlusBot(object):
    def __init__(self, score_file=None):
        self.logger = logging.getLogger("PlusPlusBot.bot.Bot")

        self.slack = SlackClient(os.environ.get('SLACK_BOT_TOKEN'), self.logger)
        self.scorekeeper = ScoreKeeper(score_file)
        self.logger.debug("Initialised application instance")

    def listen(self):
        self.slack.listen_for_actions({
            "@[0-9A-Z]{6} ++": (self.scorekeeper.plusplus, "Increment the users score"),
            "@[0-9A-Z]{6} --": (self.scorekeeper.minusminus, "Decrement the users score"),
            "@[0-9A-Z]{6} set [0-9]+": (self.scorekeeper.overwrite, "Manually set the users score"),
            "@{me} leaderboard": (self.scorekeeper.leaderboard, "Shows all the users scores"),
            "@{me} history": (self.scorekeeper.history, "Shows the last few actions"),
            "@{me} export": (self.scorekeeper.export, "Export leaderboard in CSV"),
        })
