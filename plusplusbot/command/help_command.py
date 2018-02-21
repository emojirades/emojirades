from plusplusbot.command.commands import Command
import plusplusbot.command.command_registry


class HelpCommand(Command):
    pattern = "<@{me}> help"
    description = "Shows this help"

    def format_command(self, pattern):
        pattern = pattern.replace("\\", "")

        for replacer in self.pattern_map.values():
            pattern = pattern.replace(replacer["pattern"], replacer["replace"])

        return pattern

    def execute(self):
        commands = plusplusbot.command.command_registry.CommandRegistry.prepare_commands()

        message = "Available commands are:\n```"
        message += "{0:<50}{1}\n".format("Command", "Help")

        for command in [c[0] for c in commands.values()]:
            message += "{0:<50}{1}\n".format(self.format_command(command.pattern), command.description)

        message += "```"
        yield (None, message)

    def __str__(self):
        return "HelpCommand"
