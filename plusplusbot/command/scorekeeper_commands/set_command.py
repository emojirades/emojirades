from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand
from plusplusbot.wrappers import admin_check


class SetCommand(ScoreKeeperCommand):
    description = "Manually set the users score"
    short_description = "Set a users score"

    patterns = (
        r"<@(?P<target_user>[0-9A-Z]+)> set (?P<new_score>-?[0-9]+)",
    )
    example = "@user set 123"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

        self.args["new_score"] = int(self.args["new_score"])

    @admin_check
    def execute(self):
        yield from super().execute()

        target_user = self.args["target_user"]
        new_score = self.args["new_score"]

        self.logger.debug("Setting {0} score to: {1}".format(target_user, new_score))
        self.scorekeeper.overwrite(self.args["channel"], target_user, new_score)

        message = "<@{0}> manually set to {1} point{2}"
        yield (None, message.format(target_user, new_score, "s" if new_score > 1 else ""))
