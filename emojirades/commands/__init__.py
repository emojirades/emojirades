from abc import ABC, abstractmethod, abstractproperty

import logging
import re
from functools import lru_cache

from emojirades.slack.event import Event


@lru_cache(maxsize=1024)
def get_compiled_pattern(pattern_str):
    return re.compile(pattern_str, re.DOTALL)


class BaseCommand(ABC):
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

        if event.original_channel != event.channel:
            self.args["original_channel"] = event.original_channel

        if event.original_player_id != event.player_id:
            self.args["original_user"] = event.original_player_id

        # Perform the command's actual match
        for pattern_raw in self.patterns:
            pattern_str = (
                pattern_raw.format(me=self.slack.bot_id)
                if "{me}" in pattern_raw
                else pattern_raw
            )

            pattern = get_compiled_pattern(pattern_str)

            self.logger.debug(
                "Matching '%s' against '%s'",
                pattern_str,
                event.text,
            )

            match = pattern.match(event.text)

            if not match:
                self.logger.debug(
                    "Failed to match '%s' against '%s'",
                    pattern_str,
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
        for pattern_raw in cls.patterns:
            pattern_str = pattern_raw.format(**kwargs)
            pattern = get_compiled_pattern(pattern_str)

            if pattern.match(text):
                return True

        return False

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
