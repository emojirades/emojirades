from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_check


class GameStatus(GameStateCommand):
    pattern = "<@{me}> game status"
    description = "Prints out the game status"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.masked_emojirade = True

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_check
    def execute(self):
        for i in super().execute():
            yield i

        status = self.gamestate.game_status(self.args["channel"])

        pretty_status = []

        for k, v in sorted(status.items()):
            if k == "old_winner" or k == "winner":
                if v is None:
                    v = "Not Set"
                else:
                    v = "<@{0}>".format(v)
            elif k == "admins":
                v = ", ".join(["<@{0}>".format(i) for i in v])
            elif k == "emojirade":
                if v is None:
                    v = "Not Set"
                else:
                    if self.masked_emojirade:
                        v = "*****"
                    else:
                        v = " | ".join(["`{0}`".format(i) for i in v])
            else:
                v = str(v)

            pretty_status.append((k, v))

        yield (None, "\n".join("{0}: {1}".format(k, v) for k, v in pretty_status))
