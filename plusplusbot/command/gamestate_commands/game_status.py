import re

from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_check


class GameStatus(GameStateCommand):
    pattern = "<@{me}> game status"
    description = "Prints out the game status"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["user"] = event["user"]
        self.args["channel"] = event["channel"]

    @admin_check
    def execute(self):
        status = self.gamestate.game_status(self.args["channel"])

        pretty_status = []

        for k, v in sorted(status.items()):
            if k == "old_winner" or k == "winner":
                v = "<@{0}>".format(v)
            elif k == "admins":
                v = ", ".join(["<@{0}>".format(i) for i in v])
            elif k == "emojirade":
                v = "`{0}`".format(v)
            else:
                v = str(v)

            pretty_status.append((k, v))

        yield (None, "\n".join("{0}: {1}".format(k, v) for k, v in pretty_status))
