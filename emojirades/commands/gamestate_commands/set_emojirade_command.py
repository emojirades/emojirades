import random

from emojirades.wrappers import only_in_progress, only_as_direct_message
from emojirades.checks import emojirade_is_banned
from emojirades.commands import BaseCommand


class SetEmojiradeCommand(BaseCommand):
    description = "Sets the new emojirade to be guessed"

    patterns = (r"^(E|e)mojirade[s]* (?P<emojirade>.+)",)

    examples = [
        ("emojirade foo", "Sets the new emojirade to 'foo'"),
        (
            "emojirade foo | bar",
            "Sets the new emojirade to 'foo' with 'bar' alternative",
        ),
    ]

    def prepare_args(self, event):
        super().prepare_args(event)

        # No matter what the final channel is, save the original one
        # This will override the 'original_channel' from an admin override
        # /shrug
        self.args["original_channel"] = self.args["channel"]

        # Figure out the channel to use
        self.args["channel"] = self.gamestate.get_pending_channel(self.args["user"])

    @only_as_direct_message
    @only_in_progress
    def execute(self):
        yield from super().execute()

        user = self.args["user"]
        channel = self.args["channel"]

        if channel is None:
            yield (None, "There is no game waiting for an emojirade from you!")
            return

        previous_winner, current_winner = self.gamestate.winners(channel)

        if user != previous_winner:
            yield (
                None,
                f"Err <@{user}> it's not your turn to provide the new 'rade :sweat:",
            )
            return

        if emojirade_is_banned(self.args["emojirade"]):
            yield (
                None,
                "Sorry, but that emojirade contained a banned word/phrase :no_good:, try again?",
            )
            return

        # Break the alternatives out
        raw_emojirades = [i.strip() for i in self.args["emojirade"].split("|")]

        self.gamestate.set_emojirade(channel, raw_emojirades, user)

        # DM the winner with the new emojirade
        if len(raw_emojirades) > 1:
            alternatives = ", with alternatives " + " OR ".join(
                [f"`{i}`" for i in raw_emojirades[1:]]
            )
        else:
            alternatives = ""

        emojirades = f"`{raw_emojirades[0]}`{alternatives}"

        yield (
            current_winner,
            f"Hey, <@{previous_winner}> made the emojirade {emojirades}, good luck!",
        )

        # Let the user know their 'rade has been accepted
        yield (
            previous_winner,
            {
                "func": "reactions_add",
                "kwargs": {
                    "name": random.choice(["+1", "ok"]),
                    "timestamp": self.args["ts"],
                },
            },
        )

        # Let everyone else know
        yield (channel, f":mailbox: 'rade sent to <@{current_winner}>")
