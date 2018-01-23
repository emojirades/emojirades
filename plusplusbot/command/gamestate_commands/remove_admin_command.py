import re

from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_check


class RemoveAdmin(GameStateCommand):
    pattern = "<@{me}> demote <@([0-9A-Z]+)>"
    description = "Removes a user from the admins group"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["user"] = event["user"]
        self.args["channel"] = event["channel"]

        rendered_pattern = self.pattern.format(me=self.slack.bot_id)
        self.args["admin"] = re.match(rendered_pattern, event["text"]).group(1)

    @admin_check
    def execute(self):
        if self.gamestate.remove_admin(self.args["channel"], self.args["admin"]):
            yield (None, "<@{user}> has demoted <@{admin}> to a pleb :cold_sweat:".format(**self.args))
        else:
            yield (None, "<@{admin}> isn't an admin :face_with_rolling_eyes:".format(**self.args))