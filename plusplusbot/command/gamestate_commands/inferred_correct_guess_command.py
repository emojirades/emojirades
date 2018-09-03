from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import only_actively_guessing

import random


class InferredCorrectGuess(GameStateCommand):
    pattern = None
    description = "Takes the user that send the event as the winner, this is only ever fired internally"
    first_emojis = [
        ":tada:",
        ":first_place_medal:",
        ":sunglasses:",
        ":nerd_face:",
        ":birthday:",
        ":beers:",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)
        self.args["target_user"] = self.args["user"]

    @only_actively_guessing
    def execute(self):
        for i in super().execute():
            yield i

        state = self.gamestate.state[self.args["channel"]]

        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])
        score, is_first = self.scorekeeper.plusplus(self.args["channel"], self.args["target_user"])

        if is_first:
            emoji = " {0}".format(random.choice(self.first_emojis))
        else:
            emoji = ""

        yield (None, "<@{0}>++".format(state["winner"]))
        yield (None, "Congrats <@{0}>, you're now at {1} point{2}{3}".format(state["winner"], score, "s" if score > 1 else "", emoji))
        yield (state["old_winner"], "You'll now need to send me the new 'rade for <@{0}>".format(state["winner"]))
        yield (state["old_winner"], "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")
