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
        yield (None, self.gamestate.game_status(self.args["channel"]))
