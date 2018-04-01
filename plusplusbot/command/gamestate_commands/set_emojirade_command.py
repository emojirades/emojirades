from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import only_in_progress

import re


class SetEmojirade(GameStateCommand):
    pattern = "^emojirade (.+)$"
    description = "Sets the current Emojirade to be guessed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["user"] = event["user"]
        self.args["emojirade"] = re.match(self.pattern, event["text"]).group(1)

        # Figure out the channel to use
        # TODO: Decide if we should be getting the user to enter the channel or not?
        for channel_name, channel in self.gamestate.state.items():
            if channel["step"] == "waiting":
                self.args["channel"] = channel_name
                break
        else:
            self.args["channel"] = None

    @only_in_progress
    def execute(self):
        if self.args["user"] != self.gamestate.state[self.args["channel"]]["old_winner"]:
            yield (None, "Err <@{user}> it's not your turn to provide the new 'rade :sweat:")
            raise StopIteration

        if self.args["channel"] is None:
            yield (user, "We were unable to figure out the correct channel, please raise this issue!")
            raise StopIteration

        self.gamestate.set_emojirade(self.args["channel"], self.args["emojirade"])

        winner = self.gamestate.state[self.args["channel"]]["winner"]

        # DM the winner with the new rade
        yield (winner, "Hey, <@{user}> made the 'rade `{emojirade}`, good luck!".format(**self.args))

        # Let everyone else know
        yield (self.args["channel"], ":mailbox: 'rade sent to <@{winner}>".format(winner=winner))
