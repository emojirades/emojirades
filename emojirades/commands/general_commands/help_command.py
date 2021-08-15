from emojirades.commands import BaseCommand


class HelpCommand(BaseCommand):
    description = "Shows this help"

    patterns = (r"<@{me}> help",)

    examples = [
        ("<@{me}> help", "Shows this help"),
    ]

    def __init__(self, *args, commands, **kwargs):
        self.commands = commands
        super().__init__(*args, **kwargs)

    def execute(self):
        yield from super().execute()

        # Calculate the longest example & description
        longest_description = 0
        longest_example = 0

        for command in self.commands.values():
            for example, description in command.examples:
                description_length = len(description)
                example_length = len(example)

                if description_length > longest_description:
                    longest_description = description_length

                if example_length > longest_example:
                    longest_example = example_length

        yield (None, "Available commands are:\n")
        message = f"```\n{'Example':<{longest_example}} {'Description':<{longest_description}}\n"

        for command in self.commands.values():
            for example, description in command.examples:
                if len(description) > longest_description:
                    description = f"{description[0:longest_description]}..."

                if len(example) > longest_example:
                    example = f"{example[0:longest_example]}..."

                message += f"{example:<{longest_example}} {description:<{longest_description}}\n"

        message += "```"
        yield (None, message)

        game_admins = self.gamestate.get_admins(self.args["channel"])
        admins_names = [self.slack.pretty_name(i) for i in game_admins]
        yield (None, "Game Admins: " + ", ".join(admins_names))

    def __str__(self):
        return "HelpCommand"
