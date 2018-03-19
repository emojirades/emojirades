from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import only_in_progress

import re

class CorrectGuess(GameStateCommand):
    pattern = "<@([0-9A-Z]+)>[\s]*\+\+"
    description = "Indicates the player has correctly guessed!"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"]).group(1)
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @only_in_progress
    def execute(self):
        if self.args["user"] == self.args["target_user"]:
            yield (None, "You're not allowed to award yourself the win >.>")
            raise StopIteration

        if self.args["user"] != self.gamestate.state[self.args["channel"]]["old_winner"]:
            yield (None, "You're not the old winner, stop awarding other people the win >.>")
            raise StopIteration

        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])
        yield (None, "<@{target_user}>++".format(**self.args))
        yield (self.args["user"], "You'll now need to send me the new 'rade for <@{target_user}>".format(**self.args))
        yield (self.args["user"], "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")
