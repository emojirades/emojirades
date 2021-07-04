import random

from emojirades.wrappers import only_guessing
from emojirades.commands import BaseCommand


class CorrectGuessCommand(BaseCommand):
    description = (
        "Manually award a player the win, when automated inferrence didn't work"
    )

    patterns = (r"<@(?P<target_user>[0-9A-Z]+)>[\s]*\+\+",)

    examples = [
        ("@winner ++", "Manually award a player the win"),
    ]

    position_emojis = {
        1: ["first_place_medal"],
        2: ["second_place_medal"],
        3: ["third_place_medal"],
    }

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

    custom_messages = {
        1000: "Ok {winner} just give up already, you've won the game",
        500: ":tada::tada: Ladies and gentlemen {winner} has daym done it again :tada::tada:",
        400: ":trophy: This is a big milestone {winner}, you should feel proud",
        300: "Third century's the charm they say {winner}, congrats :sunglasses:",
        200: "Not going to lie {winner} this is pretty impressive",
        100: "Triple digits {winner}! Not everyone makes it this far! :tada:",
        50: "50 points! That's a big milestone {winner}, 100's within your grasp!",
    }

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

        emoji = random.choice(
            self.other_emojis + self.position_emojis.get(position, [])
        )
        emoji_text = f" :{emoji}:"

        if state.get("first_guess", False):
            yield (
                None,
                "Holy bejesus Batman :bat::man:, they guessed it in one go! :clap:",
            )

        if self.args["inferred"]:
            yield (None, f"<@{state['winner']}>++")

        # Build the score message
        if score in self.custom_messages:
            prefix = self.custom_messages[score].format(winnder=state["winner"])
        elif score % 50 == 0:
            prefix = (
                f"Another day, another 50 point milestone for <@{state['winner']}> "
                ":chart_with_upwards_trend:"
            )
        else:
            prefix = f"Congrats <@{state['winner']}>"

        yield (
            None,
            f"{prefix}, you're now at {score} point{'s' if score > 1 else ''}{emoji_text}",
        )

        yield (None, f"The correct emojirade was `{first_emojirade}`{alternatives}")

        yield (
            state["old_winner"],
            f"You'll now need to send me the new 'rade for <@{state['winner']}>",
        )
        yield (
            state["old_winner"],
            "Please reply back in the format `emojirade Point Break` "
            "if `Point Break` was the new 'rade",
        )
