from emojirades.wrappers import only_guessing
from emojirades.commands import BaseCommand

import random


class CorrectGuessCommand(BaseCommand):
    description = (
        "Manually award a player the win, when automated inferrence didn't work"
    )

    patterns = (r"<@(?P<target_user>[0-9A-Z]+)>[\s]*\+\+",)

    examples = [
        ("@winner ++", "Manually award a player the win"),
    ]

    first_emojis = ["first_place_medal"]
    second_emojis = ["second_place_medal"]
    third_emojis = ["third_place_medal"]

    other_emojis = [
        "tada",
        "sunglasses",
        "nerd_face",
        "birthday",
        "beers",
    ]

    reaction_emojis = [
        "tada",
        "clap",
        "+1",
        "ok_hand",
        "champagne",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)
        self.args["inferred"] = False

    @only_guessing
    def execute(self):
        yield from super().execute()

        state = self.gamestate.state[self.args["channel"]]

        if not self.args["inferred"]:
            if self.args["target_user"] in (state["old_winner"], state["winner"]):
                yield (None, "You're not allowed to award current players the win >.>")
                return

            if self.args["user"] != state["winner"]:
                yield (
                    None,
                    "You're not the current winner, stop awarding other people the win >.>",
                )
                return

        # Save a copy of the emojirade, as below clears it
        raw_emojirades = [i.replace("`", "") for i in state["emojirade"]]
        first_emojirade = raw_emojirades.pop(0)

        if raw_emojirades:
            alternatives = ", with alternatives " + " OR ".join(
                [f"`{i}`" for i in raw_emojirades]
            )
        else:
            alternatives = ""

        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])
        score, position = self.scorekeeper.plusplus(
            self.args["channel"], self.args["target_user"]
        )

        if self.args["inferred"]:
            yield (
                None,
                {
                    "func": "reactions_add",
                    "kwargs": {
                        "name": random.choice(self.reaction_emojis),
                        "timestamp": self.args["ts"],
                    },
                },
            )

        if position == 1:
            emoji = random.choice(self.first_emojis + self.other_emojis)
        elif position == 2:
            emoji = random.choice(self.second_emojis + self.other_emojis)
        elif position == 3:
            emoji = random.choice(self.third_emojis + self.other_emojis)
        else:
            emoji = random.choice(self.other_emojis)

        emoji = f" :{emoji}:"

        if state.get("first_guess", False):
            yield (
                None,
                "Holy bejesus Batman :bat::man:, they guessed it in one go! :clap:",
            )

        if self.args["inferred"]:
            yield (None, f"<@{state['winner']}>++")

        # Build the score message
        if score == 1000:
            prefix = (
                f"Ok <@{state['winner']}> just give up already, you've won the game"
            )
        elif score == 500:
            prefix = f":tada::tada: Ladies and gentlemen <@{state['winner']}> has daym done it again :tada::tada:"
        elif score == 400:
            prefix = f":trophy: This is a big milestone <@{state['winner']}>, you should feel proud"
        elif score == 300:
            prefix = f"Third century's the charm they say <@{state['winner']}>, congrats :sunglasses:"
        elif score == 200:
            prefix = f"Not going to lie <@{state['winner']}> this is pretty impressive"
        elif score == 100:
            prefix = f"Triple digits <@{state['winner']}>! Not everyone makes it this far! :tada:"
        elif score % 50 == 0:
            prefix = f"Another day, another 50 point milestone for <@{state['winner']}> :chart_with_upwards_trend:"
        else:
            prefix = f"Congrats <@{state['winner']}>"

        yield (
            None,
            f"{prefix}, you're now at {score} point{'s' if score > 1 else ''}{emoji}",
        )

        yield (None, f"The correct emojirade was `{first_emojirade}`{alternatives}")

        yield (
            state["old_winner"],
            f"You'll now need to send me the new 'rade for <@{state['winner']}>",
        )
        yield (
            state["old_winner"],
            "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade",
        )
