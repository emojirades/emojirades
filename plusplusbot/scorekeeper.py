import io
import re
import csv
import logging

from collections import defaultdict

from plusplusbot.command.commands import Command
from plusplusbot.handlers import get_configuration_handler

module_logger = logging.getLogger("PlusPlusBot.scorekeeper")

leaderboard_limit = 10
history_limit = 5


def get_handler(filename):
    class ScoreKeeperConfigurationHandler(get_configuration_handler(filename)):
        """
        Handles CRUD for the ScoreKeeper configuration file
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def load(self):
            bytes_content = super().load()

            if bytes_content is None:
                return None

            score_file = io.StringIO(bytes_content.decode("utf-8"))

            return {user: int(score) for (user, score) in csv.reader(score_file)}

        def save(self, scores):
            output = io.StringIO()

            writer = csv.writer(output)
            writer.writerows(scores.items())

            bytes_content = output.getvalue().encode("utf-8")

            super().save(bytes_content)

    return ScoreKeeperConfigurationHandler(filename)


class ScoreKeeper(object):
    def __init__(self, filename):
        self.logger = logging.getLogger("PlusPlusBot.scorekeeper.ScoreKeeper")
        self.config = get_handler(filename)
        self.scoreboard = defaultdict(int)
        self.history = []

        if filename:
            existing_state = self.config.load()

            if existing_state is not None:
                self.scoreboard.update(existing_state)
                self.logger.info("Loaded scores from {0}".format(filename))

    def plusplus(self, user):
        self.scoreboard[user] += 1
        self.history.append((user, "++"))
        self.save()

    def minusminus(self, user):
        self.scoreboard[user] -= 1
        self.history.append((user, "--"))
        self.save()

    def overwrite(self, user, score):
        self.scoreboard[user] = score
        self.history.append((user, score))
        self.save()

    def leaderboard(self, limit=leaderboard_limit):
        return sorted(self.scoreboard.items(), key=lambda i: (i[1], i[0]), reverse=True)[:limit]

    def history(self, limit=history_limit):
        return self.history[::-1][:limit]

    def save(self):
        self.config.save(self.scoreboard)
