from abc import ABC, abstractmethod, abstractproperty

import logging
import re

from emojirades.slack.event import Event


class BaseCommand(ABC):
    # pylint: disable=line-too-long
    user_override_regex = re.compile(
        r".*(?P<override_cmd>[\s]+player=[\s]*(<@(?P<user_override>[0-9A-Z]+)>)).*"
    )
    channel_override_regex = re.compile(
        r".*(?P<override_cmd>[\s]+channel=[\s]*(<#(?P<channel_override>[0-9A-Z]+)\|(?P<channel_name>[0-9A-Za-z_-]+)>)).*"
    )
    # pylint: enable=line-too-long

    def __init__(self, event: Event, workspace: dict):
        self.logger = logging.getLogger("EmojiradesBot.Command")

        self.scorekeeper = workspace["scorekeeper"]
        self.gamestate = workspace["gamestate"]
        self.slack = workspace["slack"]

        self.args = {}
        self.prepare_args(event)

        self.pattern_map = [
            {"pattern": "<@{me}>", "replace": f"@{self.slack.bot_name}"},
            {"pattern": "<@([0-9A-Z]+)>", "replace": "@player"},
            {"pattern": "(-?[0-9]+)", "replace": "<numeric score>"},
        ]

        self.print_performed_by = False

    def prepare_args(self, event: Event):
        self.args["channel"] = event.channel
        self.args["user"] = event.player_id
        self.args["ts"] = event.ts

        # Perform the channel override if it matches
        channel_override_match = BaseCommand.channel_override_regex.match(event.text)

        if channel_override_match:
            new_channel = channel_override_match.groupdict()["channel_override"]

            event.channel = new_channel

            if event.is_game_channel:
                # Verify that the user is an admin of the target channel
                if self.gamestate.is_admin(event.channel, self.args["user"]):
                    # User is an admin, allow the override
                    self.args["original_channel"] = self.args["channel"]
                    self.args["channel"] = event.channel

                    event.text = event.text.replace(
                        channel_override_match.groupdict()["override_cmd"], ""
                    )
                else:
                    # User is not an admin, roll back and ignore override
                    event.channel = self.args["channel"]
            else:
                # We cannot verify admin status of the target channel
                # Roll back and ignore the override
                event.channel = self.args["channel"]

        # Only check for user override if admin
        # The event will be set to the desired channel above if needed, so the is_game_channel
        # should pass if overridden
        if event.is_game_channel and self.gamestate.is_admin(
            self.args["channel"], self.args["user"]
        ):
            # Perform the user override if it matches
            user_override_match = BaseCommand.user_override_regex.match(event.text)

            if user_override_match:
                self.args["original_user"] = self.args["user"]
                self.args["user"] = user_override_match.groupdict()["user_override"]

                event.text = event.text.replace(
                    user_override_match.groupdict()["override_cmd"], ""
                )

        # Perform the command's actual match
        patterns = tuple(
            i.format(me=self.slack.bot_id) if "{me}" in i else i for i in self.patterns
        )

        for pattern in patterns:
            self.logger.debug(
                "Matching '%s' against '%s'",
                pattern,
                event.text,
            )

            match = re.compile(pattern, re.DOTALL).match(event.text)

            if not match:
                self.logger.debug(
                    "Failed to match '%s' against '%s'",
                    pattern,
                    event.text,
                )

            if hasattr(match, "groupdict"):
                self.args.update(match.groupdict())
                break

    def execute(self):
        if self.args.get("original_user"):
            shadow_user = f" (aka <@{self.args['original_user']}>)"
        else:
            shadow_user = ""

        if self.print_performed_by:
            # We leave channel none here to return on the channel the original message came in on
            yield (
                None,
                f"This action was performed by <@{self.args['user']}>{shadow_user}",
            )

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
    def examples(self):
        pass

    def __str__(self):
        return type(self).__name__
