from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import only_guessing

import random


class InferredCorrectGuess(GameStateCommand):
    description = "Takes the user that send the event as the winner, this is only ever fired internally"
    short_description = "Internally awards a win"

    patterns = tuple()
    example = None

    first_emojis = [
        ":first_place_medal:",
    ]

    second_emojis = [
        ":second_place_medal:",
    ]

    third_emojis = [
        ":third_place_medal:",
    ]

    other_emojis = [
        ":tada:",
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
        first_emojirade = raw_emojirades[0]

        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])
        score, position = self.scorekeeper.plusplus(self.args["channel"], self.args["target_user"])

        if position == 1:
            emoji = random.choice(self.first_emojis + self.other_emojis)
        elif position == 2:
            emoji = random.choice(self.second_emojis + self.other_emojis)
        elif position == 3:
            emoji = random.choice(self.third_emojis + self.other_emojis)
        else:
            emoji = random.choice(self.other_emojis)

        emoji = " {0}".format(emoji)

        if len(raw_emojirades) > 1:
            alternatives = ", with alternatives " + " OR ".join(["`{0}`".format(i) for i in raw_emojirades[1:]])
        else:
            alternatives = ""

        if state.get("first_guess", False):
            yield(None, "Holy bejesus Batman :bat::man:, they guessed it in one go! :clap:")

        yield (None, "<@{0}>++".format(state["winner"]))
        yield (None, "Congrats <@{0}>, you're now at {1} point{2}{3}".format(state["winner"], score, "s" if score > 1 else "", emoji))
        yield (None, "The correct emojirade was `{0}`{1}".format(first_emojirade, alternatives))

        yield (state["old_winner"], "You'll now need to send me the new 'rade for <@{0}>".format(state["winner"]))
        yield (state["old_winner"], "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")
