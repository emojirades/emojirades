from abc import ABC, abstractmethod, abstractproperty
import re
import logging


class Command(ABC):
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


class PlusPlusCommand(Command):

    pattern = "<@([0-9A-Z].*)> \+\+"
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


class MinusMinusCommand(Command):

    pattern = "<@([0-9A-Z].*)> --"
    description = "Decrement the users score"

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"])[1]
        self.args["user"] = event["user"]

    def execute(self):

        target_user = self.args["target_user"]

        if self.args["user"] != target_user:
            self.logger.debug("Incrementing user's score: {}".format(target_user))
            self.scorekeeper.minusminus(target_user)
            self.scorekeeper.flush()

            score = self.scorekeeper.scoreboard[target_user]

            return "Oops <@{}>, you're now at {} point{}".format(target_user,
                                                                     score,
                                                                     "s" if score > 1 else "")


class LeaderboardCommand(Command):

    pattern = "<@({me})> leaderboard"
    description = "Shows all the users scores"

    def execute(self):
        self.logger.debug("Printing leaderboard: {}".format(self.scorekeeper.leaderboard()))

        leaderboard = self.scorekeeper.leaderboard()

        return "\n".join(["{}. <@{}> [{} point{}]".format(index + 1, *user, "s" if user[1] > 1 else "")
                          for index, user in enumerate(leaderboard)])
