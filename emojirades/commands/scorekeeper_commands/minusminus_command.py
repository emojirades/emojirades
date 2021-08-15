from emojirades.commands import BaseCommand
from emojirades.wrappers import admin_check


class MinusMinusCommand(BaseCommand):
    description = "Decrement the users score"

    patterns = (r"<@(?P<target_user>[0-9A-Z]+)>[\s]*--",)

    examples = [
        ("@user --", "Decrement users score"),
    ]

    @admin_check
    def execute(self):
        yield from super().execute()

        target_user = self.args["target_user"]

        self.logger.debug("Decrementing user's score: %s", target_user)
        self.scorekeeper.minusminus(self.args["channel"], target_user)

        _, score = self.scorekeeper.position_on_scoreboard(
            self.args["channel"], target_user
        )

        yield (
            None,
            f"Oops <@{target_user}>, you're now at {score} point{'s' if score > 1 else ''}",
        )
