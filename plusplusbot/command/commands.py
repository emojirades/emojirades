from abc import ABC, abstractmethod, abstractproperty

import logging
import re


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

    def __init__(self, slack, event, **kwargs):
        self.logger = logging.getLogger("PlusPlusBot.Command")

        self.slack = slack

        self.scorekeeper = kwargs["scorekeeper"]
        self.gamestate = kwargs["gamestate"]

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
