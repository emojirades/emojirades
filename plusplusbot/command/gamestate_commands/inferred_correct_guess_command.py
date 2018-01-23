from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import only_in_progress


class InferredCorrectGuess(GameStateCommand):
    pattern = None
    description = "Takes the user that send the event as the winner, this is only ever fired internally"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = event["user"]
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @only_in_progress
    def execute(self):
        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])

        old_winner = self.gamestate.state[self.args["channel"]]["old_winner"]

        yield (None, "<@{target_user}>++".format(**self.args))
        yield (old_winner, "You'll now need to send me the new 'rade for <@{target_user}>".format(**self.args))
        yield (old_winner, "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")