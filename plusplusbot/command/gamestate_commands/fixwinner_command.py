from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_or_old_winner_check


class FixWinner(GameStateCommand):
    patterns = [
        "<@{me}> fixwinner <@(?P<winner>[0-9A-Z]+)>",
    ]

    description = "Resets the currently awarded win to another player (in case of a ninja or something)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_or_old_winner_check
    def execute(self):
        for i in super().execute():
            yield i

        loser, winner = self.gamestate.fixwinner(self.args["channel"], self.args["winner"])

        if loser is None or winner is None:
            yield (None, "Failed to fix the winner, no scores have been updated, please fix manually :(")
            raise StopIteration

        yield (None, "<@{0}>--".format(loser))
        self.scorekeeper.minusminus(self.args["channel"], loser)

        yield (None, "<@{0}>++".format(winner))
        self.scorekeeper.plusplus(self.args["channel"], winner)

        yield (None, "Sorry <@{0}>! <@{1}> has decided to award <@{2}> the win :smiling_imp:".format(loser, self.args["user"], winner))
