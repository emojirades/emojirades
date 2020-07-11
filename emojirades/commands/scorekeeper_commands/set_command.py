from emojirades.commands import BaseCommand
from emojirades.wrappers import admin_check


class SetCommand(BaseCommand):
    description = "Manually set the users score"

    patterns = (r"<@(?P<target_user>[0-9A-Z]+)> set (?P<new_score>-?[0-9]+)",)

    examples = [
        ("@user set 123", "Set a users score"),
    ]

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

        self.logger.debug(f"Setting {target_user} score to: {new_score}")
        self.scorekeeper.overwrite(self.args["channel"], target_user, new_score)

        yield (
            None,
            f"<@{target_user}> manually set to {new_score} point{'s' if new_score > 1 else ''}",
        )
