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

    def __init__(self, scorekeeper, slack, event):
        self.logger = logging.getLogger("PlusPlusBot.Command")

        self.scorekeeper = scorekeeper
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
    def prepare_commands(cls):
        return {command.pattern: (command, command.description) for command in commands}


class PlusPlusCommand(Command):
    pattern = "<@([0-9A-Z]+)>[\s]*\+\+"
    description = "Increment the users score"

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"])[1]
        self.args["user"] = event["user"]

    def execute(self):
        target_user = self.args["target_user"]

        if self.args["user"] == target_user:
            return ":thinking_face: you're not allowed to award points to yourself..."

        if self.slack.is_bot(target_user):
            return ":thinking_face: robots aren't allowed to play Emojirades!"

        self.logger.debug("Incrementing user's score: {}".format(target_user))
        self.scorekeeper.plusplus(target_user)
        self.scorekeeper.flush()

        score = self.scorekeeper.scoreboard[target_user]

        message = "Congrats <@{0}>, you're now at {1} point{2}"
        return message.format(target_user, score, "s" if score > 1 else "")

    def __str__(self):
        return "PlusPlusCommand"


class SetCommand(Command):
    pattern = "<@([0-9A-Z]+)> set (-?[0-9]+)"
    description = "Manually set the users score"

    def prepare_args(self, event):
        args_matches = re.match(self.pattern, event["text"])

        self.args["target_user"] = args_matches[1]
        self.args["user"] = event["user"]
        self.args["new_score"] = args_matches[2]

    def execute(self):
        target_user = self.args["target_user"]
        new_score = int(self.args["new_score"])

        if self.args["user"] != target_user:
            self.logger.debug("Setting {} score to: {}".format(target_user, new_score))
            self.scorekeeper.overwrite(target_user, new_score)
            self.scorekeeper.flush()

            message = "<@{0}> manually set to {1} point{2}"
            return message.format(target_user, new_score, "s" if new_score > 1 else "")

    def __str__(self):
        return "SetCommand"


class MinusMinusCommand(Command):
    pattern = "<@([0-9A-Z]+)> --"
    description = "Decrement the users score"

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"])[1]
        self.args["user"] = event["user"]

    def execute(self):
        target_user = self.args["target_user"]

        if self.args["user"] == target_user:
            return ":thinking_face: you're not allowed to deduct points from yourself..."

        if self.slack.is_bot(target_user):
            return ":thinking_face: robots aren't allowed to play Emojirades!"

        self.logger.debug("Decrementing user's score: {}".format(target_user))
        self.scorekeeper.minusminus(target_user)
        self.scorekeeper.flush()

        score = self.scorekeeper.scoreboard[target_user]

        message = "Oops <@{0}>, you're now at {1} point{2}"
        return message.format(target_user, score, "s" if score > 1 else "")

    def __str__(self):
        return "MinusMinusCommand"


class LeaderboardCommand(Command):
    pattern = "<@{me}> leaderboard"
    description = "Shows all the users scores"

    def execute(self):
        leaderboard = self.scorekeeper.leaderboard()

        self.logger.debug("Printing leaderboard: {0}".format(leaderboard))

        return "\n".join(["{0}. <@{1}> [{2} point{3}]".format(index + 1, name, score, "s" if score > 1 else "")
                          for index, (name, score) in enumerate(leaderboard)])

    def __str__(self):
        return "LeaderboardCommand"


class HistoryCommand(Command):
    pattern = "<@{me}> history"
    description = "Shows the latest few actions performed"

    def execute(self):
        history = self.scorekeeper.history()

        self.logger.debug("Printing history: {0}".format(history))

        return "\n".join(["{0}. <@{1}> > '{2}'".format(index + 1, name, action)
                          for index, (name, action) in enumerate(history)])

    def __str__(self):
        return "HistoryCommand"


class HelpCommand(Command):
    pattern = "<@{me}> help"
    description = "Shows this help"

    def format_command(self, pattern):
        pattern = pattern.replace("\\", "")

        for replacer in self.pattern_map.values():
            pattern = pattern.replace(replacer["pattern"], replacer["replace"])

        return pattern

    def execute(self):
        message = "Available commands are:\n```"
        message += "{0:<50}{1}\n".format("Command", "Help")

        for command in commands:
            message += "{0:<50}{1}\n".format(self.format_command(command.pattern), command.description)

        message += "```"
        return message

    def __str__(self):
        return "HelpCommand"


commands = [
    PlusPlusCommand,
    MinusMinusCommand,
    SetCommand,
    LeaderboardCommand,
    HistoryCommand,
    HelpCommand,
]
