from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_check


class NewGame(GameStateCommand):
    patterns = (
        r"<@{me}> new[\s]*game <@(?P<old_winner>[0-9A-Z]+)> <@(?P<winner>[0-9A-Z]+)>",
    )

    description = "Initiate a new game by setting the Old Winner and the Winner"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_check
    def execute(self):
        yield from super().execute()

        if self.args["winner"] == self.args["old_winner"]:
            yield (None, "Sorry, but the old and current winner cannot be the same person (<@{winner}>)...".format(**self.args))
            return

        self.gamestate.new_game(self.args["channel"], self.args["old_winner"], self.args["winner"])
        yield (None, "<@{user}> has set the old winner to <@{old_winner}> and the winner to <@{winner}>".format(**self.args))
        yield (None, "It's now <@{old_winner}>'s turn to provide <@{winner}> with the next 'rade!".format(**self.args))
        yield (self.args["old_winner"], "You'll now need to send me the new 'rade for <@{winner}>".format(**self.args))
        yield (self.args["old_winner"], "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")
