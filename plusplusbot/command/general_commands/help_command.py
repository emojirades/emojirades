import plusplusbot.command.command_registry

from plusplusbot.command.commands import Command


class HelpCommand(Command):
    patterns = (
        r"<@{me}> help",
    )

    description = "Shows this help"

    def format_patterns(self, patterns):
        new_patterns = []

        for pattern in patterns:
            pattern = pattern.replace("\\", "")

            for i in self.pattern_map:
                pattern = pattern.replace(i["pattern"], i["replace"])

            new_patterns.append(pattern)

        return tuple(new_patterns)

    def execute(self):
        for i in super().execute():
            yield i

        commands = plusplusbot.command.command_registry.CommandRegistry.prepare_commands()

        message = "Available commands are:\n```"
        message += "{0:<15}{1:<50}{2}\n".format("Name", "Description", "Regex")

        for patterns, command in commands.items():
            patterns = self.format_patterns(patterns)

            for i, pattern in enumerate(patterns):
                desc = command.description

                if len(desc) > 48:
                    desc = "{0}...".format(desc[0:45])

                if i == 0:
                    message += "{0:<15}{1:<50}{2}\n".format(command.__name__, desc, pattern)
                else:
                    message += "{0:<15}{1:>50}{2}\n".format("", "Alternatives: ", pattern)

        message += "```"
        message += "Game Admins: " + ", ".join("<@{0}>".format(self.gamestate.game_status(self.args["channel"])["admins"]))

        yield (None, message)

    def __str__(self):
        return "HelpCommand"
