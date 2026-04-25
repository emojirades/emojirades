from emojirades.commands import BaseCommand
from emojirades.wrappers import admin_check


class RemoveAdminCommand(BaseCommand):
    description = "Removes a user from the admins group"

    patterns = (r"<@{me}> demote <@(?P<admin>[0-9A-Z]+)>",)

    examples = [
        ("<@{me}> demote @admin", "Demote an admin"),
    ]

    @admin_check
    def execute(self):
        yield from super().execute()

        if self.gamestate.remove_admin(self.args["channel"], self.args["admin"]):
            yield (
                None,
                f"<@{self.args['admin']}> has been demoted to a pleb :cold_sweat:",
            )
        else:
            yield (
                None,
                f"<@{self.args['admin']}> isn't an admin :face_with_rolling_eyes:",
            )
