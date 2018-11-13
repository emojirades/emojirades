from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import only_in_progress
from plusplusbot.helpers import sanitize_emojirade
from plusplusbot.checks import emojirade_is_banned


class SetEmojirade(GameStateCommand):
    patterns = [
        "^emojirade (?P<emojirade>.+)"
    ]

    description = "Sets the current Emojirade to be guessed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

        # Figure out the channel to use
        # TODO: Decide if we should be getting the user to explicitly specify the channel?
        for channel_name, channel in self.gamestate.state.items():
            if channel["step"] == "waiting":
                self.args["channel"] = channel_name
                break
        else:
            raise RuntimeError("Unable to find the correct channel for '{0}'".format(self.args["channel"]))

    @only_in_progress
    def execute(self):
        for i in super().execute():
            yield i

        if self.args["user"] != self.gamestate.state[self.args["channel"]]["old_winner"]:
            yield (None, "Err <@{user}> it's not your turn to provide the new 'rade :sweat:".format(**self.args))
            raise StopIteration

        if self.args["channel"] is None:
            yield (None, "We were unable to figure out the correct channel, please raise this issue!")
            raise StopIteration

        if emojirade_is_banned(self.args["emojirade"]):
            yield (None, "Sorry, but that emojirade contained a banned word/phrase :no_good:, try again?")
            raise StopIteration

        # Break the alternatives out and sanitize the emojirade (apply consistent sanitization)
        emojirades = [sanitize_emojirade(i) for i in self.args["emojirade"].split("|")]

        self.gamestate.set_emojirade(self.args["channel"], emojirades)

        winner = self.gamestate.state[self.args["channel"]]["winner"]

        # Let the user know their 'rade has been accepted
        yield (self.args["user"], "Thanks for that! I've let {winner} know!".format(winner=winner))

        # DM the winner with the new rade
        if len(emojirades) > 1:
            alternatives = ", with alternatives " + " OR ".join(["`{0}`".format(i) for i in emojirades[1:]])
        else:
            alternatives = ""

        yield (winner, "Hey, <@{user}> made the 'rade `{first}`{alternatives}, good luck!".format(**self.args, first=emojirades[0], alternatives=alternatives))

        # Let everyone else know
        yield (self.args["channel"], ":mailbox: 'rade sent to <@{winner}>".format(winner=winner))
