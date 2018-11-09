import plusplusbot.command.command_registry

from plusplusbot.command.commands import Command


class HelpCommand(Command):
    pattern = "<@{me}> help"
    description = "Shows this help"

    def format_command(self, pattern):
        pattern = pattern.replace("\\", "")

        for replacer in self.pattern_map.values():
            pattern = pattern.replace(replacer["pattern"], replacer["replace"])

        return pattern

    def execute(self):
        for i in super().execute():
            yield i

        commands = plusplusbot.command.command_registry.CommandRegistry.prepare_commands()

        message = "Available commands are:\n```"
        message += "{0:<50}{1}\n".format("Command", "Help")

        for command in [c[0] for c in commands.values()]:
            rendered = self.format_command(command.pattern)

            if len(rendered) > 48:
                rendered = "{0}...".format(rendered[0:45])

            message += "{0:<50}{1}\n".format(rendered, command.description)

        message += "```"
        message += "Game Admins: " + ", ".join(self.gamestate.game_status(self.args["channel"])["admins"])

        yield (None, message)

    def __str__(self):
        return "HelpCommand"
