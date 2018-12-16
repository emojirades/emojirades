import plusplusbot.command.command_registry

from plusplusbot.command.commands import Command


class HelpCommand(Command):
    description = "Shows this help"
    short_description = "Shows this help"

    patterns = (
        r"<@{me}> help",
    )
    example = "<@{me}> help"

    def format_patterns(self, patterns):
        new_patterns = []

        for pattern in patterns:
            pattern = pattern.replace("\\", "")

            for i in self.pattern_map:
                pattern = pattern.replace(i["pattern"], i["replace"])

            new_patterns.append(pattern)

        return tuple(new_patterns)

    def execute(self):
        yield from super().execute()

        commands = plusplusbot.command.command_registry.CommandRegistry.prepare_commands()

        yield (None, "Available commands are:\n")
        message = "```\n{0:<25}{1:<50}{2}\n".format("Name", "Description", "Regex")

        for patterns, command in commands.items():
            patterns = self.format_patterns(patterns)

            for i, pattern in enumerate(patterns):
                desc = command.description

                if len(desc) > 48:
                    desc = "{0}...".format(desc[0:45])

                if i == 0:
                    message += "{0:<25}{1:<50}{2}\n".format(command.__name__, desc, pattern)
                else:
                    message += "{0:<25}{1:>50}{2}\n".format("", "Alternatives:  ", pattern)

        message += "```"

        yield (None, message)
        yield (None, "Game Admins: " + ", ".join(["<@{0}>".format(i) for i in self.gamestate.game_status(self.args["channel"])["admins"]]))

    def __str__(self):
        return "HelpCommand"
