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

        longest_description = 0
        longest_example = 0

        for command in commands.values():
            description_length = len(command.short_description)
            example_length = len(command.example)

            if description_length > longest_description:
                longest_description = description_length

            if example_length > longest_example:
                longest_example = example_length

        yield (None, "Available commands are:\n")
        message = "```\n{0:<{example}} {1:<{description}}\n".format("Example",
                                                                    "Description",
                                                                    example=longest_example,
                                                                    description=longest_description)

        for command in commands.values():
            desc = command.short_description
            example = command.example

            if len(desc) > longest_description:
                desc = "{0}...".format(desc[0:longest_description])

            if len(example) > longest_example:
                example = "{0}...".format(example[0:longest_example])

            message += "{0:<{example}} {1:<{description}}\n".format(example, desc, example=longest_example, description=longest_description)

        message += "```"

        yield (None, message)
        yield (None, "Game Admins: " + ", ".join(["<@{0}>".format(i) for i in self.gamestate.game_status(self.args["channel"])["admins"]]))

    def __str__(self):
        return "HelpCommand"
