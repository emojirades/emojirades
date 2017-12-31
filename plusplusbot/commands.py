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
    pattern = "<@([0-9A-Z]+)> \+\+"
    description = "Increment the users score"

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"])[1]
        self.args["user"] = event["user"]

    def execute(self):
        target_user = self.args["target_user"]

        if self.args["user"] != target_user:
            self.logger.debug("Incrementing user's score: {}".format(target_user))
            self.scorekeeper.plusplus(target_user)
            self.scorekeeper.flush()

            score = self.scorekeeper.scoreboard[target_user]

            return "Congrats <@{}>, you're now at {} point{}".format(target_user,
                                                                     score,
                                                                     "s" if score > 1 else "")


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

            return "<@{}> now at {} point{}".format(target_user,
                                                    new_score,
                                                    "s" if new_score > 1 else "")


class MinusMinusCommand(Command):
    pattern = "<@([0-9A-Z]+)> --"
    description = "Decrement the users score"

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"])[1]
        self.args["user"] = event["user"]

    def execute(self):
        target_user = self.args["target_user"]

        if self.args["user"] != target_user:
            self.logger.debug("Decrementing user's score: {}".format(target_user))
            self.scorekeeper.minusminus(target_user)
            self.scorekeeper.flush()

            score = self.scorekeeper.scoreboard[target_user]

            return "Oops <@{}>, you're now at {} point{}".format(target_user,
                                                                     score,
                                                                     "s" if score > 1 else "")


class LeaderboardCommand(Command):
    pattern = "<@{me}> leaderboard"
    description = "Shows all the users scores"

    def execute(self):
        self.logger.debug("Printing leaderboard: {}".format(self.scorekeeper.leaderboard()))

        leaderboard = self.scorekeeper.leaderboard()

        return "\n".join(["{}. <@{}> [{} point{}]".format(index + 1, *user, "s" if user[1] > 1 else "")
                          for index, user in enumerate(leaderboard)])


class HelpCommand(Command):
    pattern = "<@{me}> help"
    description = "Shows this help"

    def format_command(self, pattern):
        #pattern = pattern.replace("{me}", self.slack.bot_id)
        pattern =pattern.replace("\\", "")

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

commands = [
    PlusPlusCommand,
    MinusMinusCommand,
    SetCommand,
    LeaderboardCommand,
    HelpCommand
]
