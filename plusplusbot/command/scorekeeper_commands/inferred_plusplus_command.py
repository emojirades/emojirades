from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand
from plusplusbot.wrappers import only_in_progress


class InferredPlusPlusCommand(ScoreKeeperCommand):
    pattern = None
    description = "Increments the users score"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = event["user"]
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @only_in_progress
    def execute(self):
        target_user = self.args["target_user"]

        self.logger.debug("Incrementing user's score: {}".format(target_user))
        self.scorekeeper.plusplus(target_user)

        score = self.scorekeeper.scoreboard[target_user]

        message = "Congrats <@{0}>, you're now at {1} point{2}"
        yield (None, message.format(target_user, score, "s" if score > 1 else ""))

    def __str__(self):
        return "InferredPlusPlusCommand"
