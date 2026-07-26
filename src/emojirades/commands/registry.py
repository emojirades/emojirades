from emojirades.commands import BaseCommand


class CommandRegistry:
    registered_commands = BaseCommand.registered_commands

    @classmethod
    def command_patterns(cls, commands=None):
        if commands is None:
            commands = cls.registered_commands

        return {Command.patterns: Command for Command in commands if Command.patterns}

    @classmethod
    def command_names(cls, commands=None):
        if commands is None:
            commands = cls.registered_commands

        return {Command.__name__: Command for Command in commands}
