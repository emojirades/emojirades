from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand
from plusplusbot.wrappers import admin_check

import re


class MinusMinusCommand(ScoreKeeperCommand):
    pattern = "<@([0-9A-Z]+)> --"
    description = "Decrement the users score"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"]).group(1)
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @admin_check
    def execute(self):
        target_user = self.args["target_user"]

        self.logger.debug("Decrementing user's score: {0}".format(target_user))
        self.scorekeeper.minusminus(target_user)

        score = self.scorekeeper.scoreboard[target_user]

        message = "Oops <@{0}>, you're now at {1} point{2}"
        yield (None, message.format(target_user, score, "s" if score > 1 else ""))
