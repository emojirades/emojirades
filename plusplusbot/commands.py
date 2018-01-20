from abc import ABC, abstractmethod, abstractproperty

import re
import logging


class Command(ABC):

    # TODO: replace hardcoded pattern with this map
    pattern_map = {
        "me": {
            "pattern": "<@{me}>",
            "replace": "@epp"
        },
        "player": {
            "pattern": "<@([0-9A-Z]+)>",
            "replace": "@player"
        },
        "score": {
            "pattern": "(-?[0-9]+)",
            "replace": "<numeric score>"
        }
    }

    def __init__(self, slack, event, handles=None):
        self.logger = logging.getLogger("PlusPlusBot.Command")

        if handles is not None:
            for handle in handles:
                if handle in kwargs:
                    setattr(self, handle, kwargs[handle])
                else:
                    raise RuntimeError("GameStateCommand requires a handle to '{0}'".format(handle))

        self.slack = slack
        self.args = {}

        self.prepare_args(event)

    def prepare_args(self, event):
        pass

    @classmethod
    def match(cls, text, **kwargs):
        return re.match(cls.pattern.format(**kwargs), text)

    @abstractproperty
    def pattern(self):
        pass

    @abstractproperty
    def description(self):
        pass

    @abstractmethod
    def execute(self):
        pass

    @classmethod
    def prepare_commands(cls, commands=None):
        if commands is None:
            commands = default_commands

        return {command.pattern: (command, command.description) for command in commands}


class HelpCommand(Command):
    pattern = "<@{me}> help"
    description = "Shows this help"

    def format_command(self, pattern):
        pattern = pattern.replace("\\", "")

        for replacer in self.pattern_map.values():
            pattern = pattern.replace(replacer["pattern"], replacer["replace"])

        return pattern

    def execute(self, commands):
        message = "Available commands are:\n```"
        message += "{0:<50}{1}\n".format("Command", "Help")

        for command in commands:
            message += "{0:<50}{1}\n".format(self.format_command(command.pattern), command.description)

        message += "```"
        return (None, message)

    def __str__(self):
        return "HelpCommand"


default_commands = [
    HelpCommand,
]
