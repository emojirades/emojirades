from emojirades.wrappers import admin_or_old_winner_check, only_not_in_progress
from emojirades.commands import BaseCommand


class FixWinnerCommand(BaseCommand):
    description = "Resets the currently awarded win to another player (in case of a ninja or something)"

    patterns = (r"<@{me}> fixwinner <@(?P<winner>[0-9A-Z]+)>",)

    examples = [
        ("<@{me}> fixwinner @other-person", "Award the win to someone else"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_or_old_winner_check
    @only_not_in_progress
    def execute(self):
        yield from super().execute()

        if (
            self.args["winner"]
            == self.gamestate.state[self.args["channel"]]["old_winner"]
        ):
            yield (None, ":face_palm: You can't award yourself the win")
            return

        if self.args["winner"] == self.gamestate.state[self.args["channel"]]["winner"]:
            yield (None, "This won't actually do anything? :shrug::face_with_monocle:")
            return

        loser, winner = self.gamestate.fixwinner(
            self.args["channel"], self.args["winner"]
        )

        if loser is None or winner is None:
            yield (
                None,
                "Failed to fix the winner, no scores have been updated, please fix manually :(",
            )
            return

        yield (None, f"<@{loser}>--")
        self.scorekeeper.minusminus(self.args["channel"], loser)

        yield (None, f"<@{winner}>++")
        self.scorekeeper.plusplus(self.args["channel"], winner)

        yield (
            None,
            f"Sorry <@{loser}>! <@{self.args['user']}> has decided to award <@{winner}> the win :smiling_imp:",
        )
