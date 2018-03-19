from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand
from plusplusbot.wrappers import only_in_progress

import re


class PlusPlusCommand(ScoreKeeperCommand):
    pattern = "<@([0-9A-Z]+)>[\s]*\+\+"
    description = "Increment the users score"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"]).group(1)
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @only_in_progress
    def execute(self):
        target_user = self.args["target_user"]

        if self.args["user"] == target_user:
            yield (None, ":thinking_face: you're not allowed to award points to yourself...")
            raise StopIteration

        if self.slack.is_bot(target_user):
            yield (None, ":thinking_face: robots aren't allowed to play Emojirades!")
            raise StopIteration

        self.logger.debug("Incrementing user's score: {}".format(target_user))
        self.scorekeeper.plusplus(target_user)

        score = self.scorekeeper.scoreboard[target_user]

        message = "Congrats <@{0}>, you're now at {1} point{2}"
        yield (None, message.format(target_user, score, "s" if score > 1 else ""))

    def __str__(self):
        return "PlusPlusCommand"
