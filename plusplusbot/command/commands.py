from abc import ABC, abstractmethod, abstractproperty

import logging
import re


class Command(ABC):
    user_override_regex = re.compile(r".*(?P<override_cmd>[\s]+player=[\s]*(<@(?P<user_override>[0-9A-Z]+)>)).*")
    channel_override_regex = re.compile(r".*(?P<override_cmd>[\s]+channel=[\s]*(<#(?P<channel_override>[0-9A-Z]+)\|(?P<channel_name>[0-9A-Za-z_-]+)>)).*")

    def __init__(self, slack, event, **kwargs):
        self.logger = logging.getLogger("PlusPlusBot.Command")

        self.slack = slack

        self.scorekeeper = kwargs["scorekeeper"]
        self.gamestate = kwargs["gamestate"]

        self.args = {}
        self.prepare_args(event)

        self.pattern_map = [
            {"pattern": "<@{me}>", "replace": "@{0}".format(self.slack.bot_name)},
            {"pattern": "<@([0-9A-Z]+)>", "replace": "@player"},
            {"pattern": "(-?[0-9]+)", "replace": "<numeric score>"},
        ]

        self.print_performed_by = False

    def prepare_args(self, event):
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

        # Only check for overrides if admin
        if self.gamestate.is_admin(self.args["channel"], self.args["user"]):
            # Perform the channel override if it matches
            channel_override_match = Command.channel_override_regex.match(event["text"])

            if channel_override_match:
                self.args["original_channel"] = self.args["channel"]
                self.args["channel"] = channel_override_match.groupdict()["channel_override"]

                event["text"] = event["text"].replace(channel_override_match.groupdict()["override_cmd"], "")

            # Perform the user override if it matches
            user_override_match = Command.user_override_regex.match(event["text"])

            if user_override_match:
                self.args["original_user"] = self.args["user"]
                self.args["user"] = user_override_match.groupdict()["user_override"]

                event["text"] = event["text"].replace(user_override_match.groupdict()["override_cmd"], "")

        # Perform the command's actual match
        patterns = tuple(i.format(me=self.slack.bot_id) if "{me}" in i else i for i in self.patterns)

        for pattern in patterns:
            self.logger.debug("Matching '{0}' against '{1}'".format(pattern, event["text"]))

            match = re.compile(pattern).match(event["text"])

            if not match:
                self.logger.debug("Failed to match '{0}' against '{1}'".format(pattern, event["text"]))

            if hasattr(match, "groupdict"):
                self.args.update(match.groupdict())
                break

    def execute(self):
        if self.args.get("original_user"):
            shadow_user = " (aka <@{0}>)".format(self.args["original_user"])
        else:
            shadow_user = ""

        if self.print_performed_by:
            # We leave channel none here to return on the channel the original message came in on
            yield (None, "This action was performed by <@{0}>{1}".format(self.args["user"], shadow_user))

    @classmethod
    def match(cls, text, **kwargs):
        return any(re.match(pattern.format(**kwargs), text) for pattern in cls.patterns)

    @property
    def description(self):
        pass

    @property
    def short_description(self):
        pass

    @property
    def patterns(self):
        pass

    @property
    def example(self):
        pass

    def __str__(self):
        return type(self).__name__
