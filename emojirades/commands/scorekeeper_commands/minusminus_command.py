from emojirades.commands import BaseCommand
from emojirades.wrappers import admin_check


class MinusMinusCommand(BaseCommand):
    description = "Decrement the users score"

    patterns = (r"<@(?P<target_user>[0-9A-Z]+)>[\s]*--",)

    examples = [
        ("@user --", "Decrement users score"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_check
    def execute(self):
        yield from super().execute()

        target_user = self.args["target_user"]

        self.logger.debug(f"Decrementing user's score: {target_user}")
        self.scorekeeper.minusminus(self.args["channel"], target_user)

        score, _ = self.scorekeeper.current_score(self.args["channel"], target_user)

        yield (
            None,
            f"Oops <@{target_user}>, you're now at {score} point{'s' if score > 1 else ''}",
        )
