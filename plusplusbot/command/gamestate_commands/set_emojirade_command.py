from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import only_in_progress, only_as_direct_message
from plusplusbot.helpers import sanitize_text
from plusplusbot.checks import emojirade_is_banned


class SetEmojirade(GameStateCommand):
    description = "Sets the new emojirade to be guessed"
    short_description = "Sets the new emojirade"

    patterns = (
        r"^emojirade[s]{0,1} (?P<emojirade>.+)",
    )
    example = "emojirade foobar"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

        # No matter what the final channel is, save the original one
        # This will override the 'original_channel' from an admin override
        # /shrug
        self.args["original_channel"] = self.args["channel"]

        # Figure out the channel to use
        for channel_name, channel in self.gamestate.state.items():
            if channel["step"] == "waiting":
                self.args["channel"] = channel_name
                break
        else:
            self.args["channel"] = None

    @only_as_direct_message
    @only_in_progress
    def execute(self):
        yield from super().execute()

        if self.args["user"] != self.gamestate.state[self.args["channel"]]["old_winner"]:
            yield (None, "Err <@{user}> it's not your turn to provide the new 'rade :sweat:".format(**self.args))
            return

        if self.args["channel"] is None:
            yield (None, "There is no current game waiting for a new emojirade!")
            return

        if emojirade_is_banned(self.args["emojirade"]):
            yield (None, "Sorry, but that emojirade contained a banned word/phrase :no_good:, try again?")
            return

        # Break the alternatives out and sanitize the emojirade (apply consistent sanitization)
        raw_emojirades = [i.strip() for i in self.args["emojirade"].split("|")]
        sanitized_emojirades = [sanitize_text(i) for i in raw_emojirades]

        self.gamestate.set_emojirade(self.args["channel"], sanitized_emojirades)

        winner = self.gamestate.state[self.args["channel"]]["winner"]

        # DM the winner with the new emojirade
        if len(raw_emojirades) > 1:
            alternatives = ", with alternatives " + " OR ".join(["`{0}`".format(i) for i in raw_emojirades[1:]])
        else:
            alternatives = ""

        msg = "Hey, <@{user}> made the emojirade `{first}`{alternatives}, good luck!".format(
            **self.args,
            first=raw_emojirades[0],
            alternatives=alternatives
        )
        yield (winner, msg)

        # Let the user know their 'rade has been accepted
        yield (self.args["user"], "Thanks for that! I've let <@{winner}> know!".format(winner=winner))

        # Let everyone else know
        yield (self.args["channel"], ":mailbox: 'rade sent to <@{winner}>".format(winner=winner))
