from emojirades.commands import BaseCommand
from emojirades.wrappers import admin_check


class SetCommand(BaseCommand):
    description = "Manually set the users score"

    patterns = (r"<@(?P<target_user>[0-9A-Z]+)> set (?P<score>-?[0-9]+)",)

    examples = [
        ("@user set 123", "Set a users score"),
    ]

    def prepare_args(self, event):
        super().prepare_args(event)

        self.args["score"] = int(self.args["score"])

    @admin_check
    def execute(self):
        yield from super().execute()

        target_user = self.args["target_user"]
        score = self.args["score"]

        self.logger.debug("Setting %s score to: %s", target_user, score)
        self.scorekeeper.overwrite(self.args["channel"], target_user, score)

        yield (
            None,
            f"<@{target_user}> manually set to {score} point{'s' if score > 1 else ''}",
        )
