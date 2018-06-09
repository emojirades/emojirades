from abc import ABC, abstractmethod, abstractproperty

import logging
import re


class Command(ABC):
    def __init__(self, slack, event, **kwargs):
        self.logger = logging.getLogger("PlusPlusBot.Command")

        self.slack = slack

        self.scorekeeper = kwargs["scorekeeper"]
        self.gamestate = kwargs["gamestate"]

        self.args = {}
        self.prepare_args(event)

        self.pattern_map = {
            "me": {
                "pattern": "<@{me}>",
                "replace": "@{0}".format(self.slack.bot_name)
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

    def prepare_args(self, event):
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

        extra_args = [
            "[\\s]*(player=[\\s]*(<@(?P<user_override>[0-9A-Z]+)>))*",
        ]

        pattern = self.pattern + ''.join(extra_args)

        if "{me}" in pattern:
            pattern = pattern.format(me=self.slack.bot_id)

        print(pattern)
        match = re.match(pattern, event["text"])

        if hasattr(match, "groupdict"):
            self.args.update(match.groupdict())

        if self.args.get("user_override") and self.gamestate.is_admin(self.args["channel"], self.args["user"]):
            self.args["original_user"] = self.args["user"]
            self.args["user"] = self.args["user_override"]

    def execute(self):
        if self.args.get("original_user"):
            shadow_user = " (aka <@{0}>)".format(self.args["original_user"])
        else:
            shadow_user = ""

        yield (None, "This action was performed by <@{0}>{1}".format(self.args["user"], shadow_user))

    @classmethod
    def match(cls, text, **kwargs):
        return re.match(cls.pattern.format(**kwargs), text)

    @abstractproperty
    def pattern(self):
        pass

    @abstractproperty
    def description(self):
        pass

    def __str__(self):
        return type(self).__name__
