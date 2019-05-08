from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import only_guessing

import random


class InferredCorrectGuess(GameStateCommand):
    description = "Takes the user that send the event as the winner, this is only ever fired internally"
    short_description = "Internally awards a win"

    patterns = tuple()
    example = None

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

    @only_guessing
    def execute(self):
        yield from super().execute()

        state = self.gamestate.state[self.args["channel"]]

        # Save a copy of the emojirade, as below clears it
        raw_emojirades = list(state["emojirade"])

        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])
        score, is_first = self.scorekeeper.plusplus(self.args["channel"], self.args["target_user"])

        if is_first:
            emoji = " {0}".format(random.choice(self.first_emojis))
        else:
            emoji = ""

        first_emojirade = raw_emojirades[0]

        if len(raw_emojirades) > 1:
            alternatives = ", with alternatives " + " OR ".join(["`{0}`".format(i) for i in raw_emojirades[1:]])
        else:
            alternatives = ""

        yield (None, "<@{0}>++".format(state["winner"]))
        yield (None, "Congrats <@{0}>, you're now at {1} point{2}{3}".format(state["winner"], score, "s" if score > 1 else "", emoji))
        yield (None, "The correct emojirade was `{0}`{1}".format(first_emojirade, alternatives))

        yield (state["old_winner"], "You'll now need to send me the new 'rade for <@{0}>".format(state["winner"]))
        yield (state["old_winner"], "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")
