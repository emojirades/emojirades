from emojirades.commands import BaseCommand
from emojirades.wrappers import admin_check


class SetAdminCommand(BaseCommand):
    description = "Promotes a user to a game admin!"

    patterns = (r"<@{me}> promote <@(?P<admin>[0-9A-Z]+)>",)

    examples = [
        ("<@{me}> promote @pleb", "Promote a user"),
    ]

    @admin_check
    def execute(self):
        yield from super().execute()

        if self.gamestate.set_admin(self.args["channel"], self.args["admin"]):
            yield (
                None,
                f"<@{self.args['admin']}> has been promoted to a game admin :tada:",
            )
        else:
            yield (
                None,
                f"<@{self.args['admin']}> is already an admin :face_with_rolling_eyes:",
            )
