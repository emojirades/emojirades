from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_check


class SetAdmin(GameStateCommand):
    patterns = (
        r"<@{me}>\\ promote\\ <@(?P<admin>[0-9A-Z]+)>",
    )

    description = "Promotes a user to a game admin!"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_check
    def execute(self):
        for i in super().execute():
            yield i

        if self.gamestate.set_admin(self.args["channel"], self.args["admin"]):
            yield (None, "<@{admin}> has been promoted to a game admin :tada:".format(**self.args))
        else:
            yield (None, "<@{admin}> is already an admin :face_with_rolling_eyes:".format(**self.args))
