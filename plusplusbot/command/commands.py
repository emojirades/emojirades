from abc import ABC, abstractmethod, abstractproperty

import logging
import re


class Command(ABC):
    user_override_regex = re.compile(".*(?P<override_cmd>[\\s]+player=[\\s]*(<@(?P<user_override>[0-9A-Z]+)>)).*")

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

        pattern = str(self.pattern)

        if "{me}" in pattern:
            pattern = pattern.format(me=self.slack.bot_id)

        # Perform the user override if it matches
        user_override_match = Command.user_override_regex.match(event["text"])

        if user_override_match and self.gamestate.is_admin(self.args["channel"], self.args["user"]):
            self.args["original_user"] = self.args["user"]
            self.args["user"] = user_override_match.groupdict()["user_override"]

            event["text"] = event["text"].replace(user_override_match.groupdict()["override_cmd"], "")

        # Perform the command's actual match
        match = re.match(pattern, event["text"])

        if hasattr(match, "groupdict"):
            self.args.update(match.groupdict())

    def execute(self):
        if self.args.get("original_user"):
            shadow_user = " (aka <@{0}>)".format(self.args["original_user"])
        else:
            shadow_user = ""

        # We leave channel none here to return on the channel the original message came in on
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
