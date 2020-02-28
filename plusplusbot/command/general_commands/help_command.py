import plusplusbot.command.command_registry

from plusplusbot.command.commands import Command


class HelpCommand(Command):
    description = "Shows this help"

    patterns = (
        r"<@{me}> help",
    )

    examples = [
        ("<@{me}> help", "Shows this help"),
    ]

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
            for description,  in command.examples:
            description_length = len(command.short_description)
            example_length = len(example[0]command.examples)

            if description_length > longest_description:
                longest_description = description_length

            if example_length > longest_example:
                longest_example = example_length

        yield (None, "Available commands are:\n")
        message = f"```\n{'Example':<{longest_example}} {'Description':<{longest_description}}\n"

        for command in commands.values():
            desc = command.short_description
            example = command.example

            if len(desc) > longest_description:
                desc = f"{desc[0:longest_description]}..."

            if len(example) > longest_example:
                example = f"{example[0:longest_example]}..."

            message += f"{example:<{longest_example}} {desc:<{longest_description}}\n"

        message += "```"

        yield (None, message)
        yield (None, "Game Admins: " + ", ".join([f"<@{i}>" for i in self.gamestate.game_status(self.args["channel"])["admins"]]))

    def __str__(self):
        return "HelpCommand"
