from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand
from plusplusbot.wrappers import admin_check


class MinusMinusCommand(ScoreKeeperCommand):
    description = "Decrement the users score"
    short_description = "Decrement users score"

    patterns = (
        r"<@(?P<target_user>[0-9A-Z]+)>[\s]*--",
    )
    example = "@user --"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_check
    def execute(self):
        yield from super().execute()

        target_user = self.args["target_user"]

        self.logger.debug("Decrementing user's score: {0}".format(target_user))
        self.scorekeeper.minusminus(self.args["channel"], target_user)

        score, _ = self.scorekeeper.current_score(self.args["channel"], target_user)

        message = "Oops <@{0}>, you're now at {1} point{2}"
        yield (None, message.format(target_user, score, "s" if score > 1 else ""))
