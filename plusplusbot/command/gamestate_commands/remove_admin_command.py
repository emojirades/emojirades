from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_check


class RemoveAdmin(GameStateCommand):
    pattern = "<@{me}> demote <@(?P<admin>[0-9A-Z]+)>"
    description = "Removes a user from the admins group"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_check
    def execute(self):
        for i in super().execute():
            yield i

        if self.gamestate.remove_admin(self.args["channel"], self.args["admin"]):
            yield (None, "<@{admin}> has been demoted to a pleb :cold_sweat:".format(**self.args))
        else:
            yield (None, "<@{admin}> isn't an admin :face_with_rolling_eyes:".format(**self.args))
