import re

from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_check


class SetAdmin(GameStateCommand):
    pattern = "<@{me}> promote <@([0-9A-Z]+)>"
    description = "Promotes a user to a game admin!"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["user"] = event["user"]
        self.args["channel"] = event["channel"]

        rendered_pattern = self.pattern.format(me=self.slack.bot_id)
        self.args["admin"] = re.match(rendered_pattern, event["text"]).group(1)

    @admin_check
    def execute(self):
        if self.gamestate.set_admin(self.args["channel"], self.args["admin"]):
            yield (None, "<@{user}> has promoted <@{admin}> to a game admin :tada:".format(**self.args))
        else:
            yield (None, "<@{admin}> is already an admin :face_with_rolling_eyes:".format(**self.args))
