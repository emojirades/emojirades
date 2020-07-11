from emojirades.commands import BaseCommand
import emojirades.commands.registry


class HelpCommand(BaseCommand):
    description = "Shows this help"

    patterns = (r"<@{me}> help",)

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

        commands = emojirades.commands.registry.CommandRegistry.command_patterns()

        # Calculate the longest example & description
        longest_description = 0
        longest_example = 0

        for command in commands.values():
            for example, description in command.examples:
                description_length = len(description)
                example_length = len(example)

                if description_length > longest_description:
                    longest_description = description_length

                if example_length > longest_example:
                    longest_example = example_length

        yield (None, "Available commands are:\n")
        message = f"```\n{'Example':<{longest_example}} {'Description':<{longest_description}}\n"

        for command in commands.values():
            for example, description in command.examples:
                if len(description) > longest_description:
                    description = f"{description[0:longest_description]}..."

                if len(example) > longest_example:
                    example = f"{example[0:longest_example]}..."

                message += f"{example:<{longest_example}} {description:<{longest_description}}\n"

        message += "```"
        yield (None, message)

        game_admins = self.gamestate.game_status(self.args["channel"])["admins"]
        admins_names = [self.slack.pretty_name(i) for i in game_admins]
        yield (None, "Game Admins: " + ", ".join(admins_names))

    def __str__(self):
        return "HelpCommand"
